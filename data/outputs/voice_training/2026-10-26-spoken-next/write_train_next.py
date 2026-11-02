"""Write kp-2001–kp-2200 source rows into a new train-pool file.

Reads spoken_scale.jsonl only to reject duplicate source text. Does not
write that file, does not fill candidates, and does not start a trainer.

The 11 bank_leftover lines are unused drafts from the 2026-10-23 scale
bank. The other lines are new situations. Licence stays unknown.
review_status stays pending_native_review. Origin stays synthetic.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter
from pathlib import Path

from claynext.models.khmer_spoken.schema import SCHEMA_VERSION

ROOT = Path(__file__).resolve().parents[4]
SCALE = ROOT / "data/khmer_spoken/workspace/spoken_scale.jsonl"
OUT = ROOT / "data/khmer_spoken/workspace/spoken_train_next.jsonl"

LICENSE_NOTES = (
    "Synthetic spoken-dialogue draft for the train pool after kp-2000. "
    "Original English line, checked against kp-001 through kp-2000. "
    "Licence unknown. Not gold. Not owner-approved. Pending native review. "
    "Not a weight update."
)
REVIEWER_NOTES = (
    "Synthetic English source only. No reference Khmer. "
    "review_status pending_native_review. Not gold."
)

STOP = frozenset(
    """
    a an the to of and or for in on at is it i you we they my your our me
    him her his she he dont don't can will just not with from that this them
    their be was were am are do did if so but then than when before after
    into out up down over about as by too very please im i'm ill i'll ive
    i've youre you're were we're its it's thats that's
    """.split()
)

# kind, emotion, speaker, listener, relationship, register, setting, category, text
RAW = """
bank_leftover	neutral	srey	ms_sothea	student_to_teacher	neutral	classroom	school	Teacher, I'll bring the signed page tomorrow morning, before class.
bank_leftover	neutral	ms_sothea	dara	teacher_to_student	formal	classroom	school	That ends the speaking practice. Hands down. Eyes here.
bank_leftover	worried	vuthy	doctor_nary	patient_to_doctor	formal	clinic	clinic	The cramp is in the calf at night, after I stand at the stall all day.
bank_leftover	neutral	doctor_nary	vuthy	doctor_to_patient	formal	clinic	clinic	Stretch before sleep. If the leg swells or goes red, that is a different visit.
bank_leftover	worried	vanna	doctor_nary	patient_to_doctor	formal	clinic	clinic	Doctor, speak a little slower. I want to repeat the instructions back.
bank_leftover	neutral	doctor_nary	vanna	doctor_to_patient	formal	clinic	clinic	Good. Say them back now. I'll correct only the part about the timing.
bank_leftover	neutral	lina	doctor_nary	patient_to_doctor	formal	clinic	clinic	Thank you. I'll bring my father tomorrow morning, before the rush.
bank_leftover	neutral	doctor_nary	lina	doctor_to_patient	formal	clinic	clinic	Come early. If the chest pain returns tonight, don't wait for morning.
bank_leftover	neutral	mother	dara	parent_to_child	neutral	home	parent_to_child	Lights out after the story, not after a second story.
bank_leftover	tender	channary	vuthy	romantic	casual	evening	romantic	Give me your bag. Your shoulder has been up by your ear all evening.
bank_leftover	neutral	vuthy	channary	romantic	casual	evening	romantic	We can be ordinary. I think that's what I came here to ask.
new_situation	neutral	vuthy	barber_houn	customer_to_barber	casual	barber	barber	Leave the top longer. The last cut made my ears look early.
new_situation	neutral	barber_houn	vuthy	barber_to_customer	casual	barber	barber	Sit straight. If you watch the phone, the neckline goes crooked.
new_situation	worried	srey	barber_houn	customer_to_barber	casual	barber	barber	A little off the ends only. I have a photo day on Monday.
new_situation	neutral	barber_houn	srey	barber_to_customer	casual	barber	barber	Close your eyes. The clippers throw hair and the fan blows it back.
new_situation	happy	lina	barber_houn	customer_to_barber	casual	barber	barber	That side matches now. Last week one ear was hiding.
new_situation	teasing	barber_houn	rith	barber_to_customer	casual	barber	barber	Hold still, champion. The mirror is not a moving target.
new_situation	worried	rith	barber_houn	customer_to_barber	casual	barber	barber	Don't take the fringe so short. My forehead burns in the yard.
new_situation	neutral	barber_houn	piseth	barber_to_customer	casual	barber	barber	The cape stays on until I brush your neck. The hairs itch later.
new_situation	tired	piseth	barber_houn	customer_to_barber	casual	barber	barber	Same shape as last month. I only came because the collar looks wild.
new_situation	neutral	barber_houn	sokha	barber_to_customer	casual	barber	barber	I am out of the bay rum. Cool water will do for the finish.
new_situation	happy	sokha	barber_houn	customer_to_barber	casual	barber	barber	The part sits where I comb it. You found the cowlick.
new_situation	worried	nita	barber_houn	customer_to_barber	casual	barber	barber	Skip the razor near the mole. It bled the last time.
new_situation	neutral	barber_houn	nita	barber_to_customer	casual	barber	barber	I will tidy around it with scissors. No blade on that spot.
new_situation	tender	channary	barber_houn	customer_to_barber	casual	barber	barber	Leave enough to tie back. The ceremony is three days away.
new_situation	neutral	barber_houn	channary	barber_to_customer	casual	barber	barber	I pinned the side so the pins don't scratch when you bow.
new_situation	neutral	dara	barber_houn	customer_to_barber	casual	barber	barber	Can the stool go lower? My chin is above your shoulder.
new_situation	teasing	barber_houn	dara	barber_to_customer	casual	barber	barber	You grew since the school haircut. I had to raise the chair twice.
new_situation	worried	bopha	barber_houn	customer_to_barber	casual	barber	barber	The buzzer tickles my neck. Tell me before you switch it on.
new_situation	neutral	barber_houn	bopha	barber_to_customer	casual	barber	barber	Done. Check the back with the small mirror before you stand.
new_situation	happy	vanna	barber_houn	customer_to_barber	casual	barber	barber	I can see both eyebrows. You evened them without me asking.
new_situation	neutral	barber_houn	vanna	barber_to_customer	casual	barber	barber	Shake the cape outside. I just swept and the floor was clean.
new_situation	worried	uncle_thon	sophea	elder_to_youth	casual	field	harvest	The sheaves on the north edge are still damp. Cut the west row first.
new_situation	neutral	sophea	uncle_thon	youth_to_elder	casual	field	harvest	I stacked the cut stalks on the canvas, grain heads pointed inward.
new_situation	tired	lina	uncle_thon	youth_to_elder	casual	field	harvest	My wrists ache from the sickle. May I switch to tying bundles?
new_situation	neutral	uncle_thon	lina	elder_to_youth	casual	field	harvest	Tie at the middle, not the heads, or the grain spills on the path.
new_situation	happy	dara	srey	friends_close	casual	field	harvest	We finished the plot by the termite mound before the sun hit the canal.
new_situation	worried	srey	dara	friends_close	casual	field	harvest	A snake skin is caught in the stubble. Step where I already walked.
new_situation	neutral	piseth	uncle_thon	youth_to_elder	casual	field	harvest	The ox cart is at the dike. I left the rope on the near wheel.
new_situation	neutral	uncle_thon	piseth	elder_to_youth	casual	field	harvest	Load the dry bundles first. The wet ones stay until afternoon.
new_situation	tender	grandma_yeay	vanna	grandparent_to_grandchild	casual	field	harvest	Drink from the clay jar in the shade. The field water is for the plants.
new_situation	neutral	vanna	grandma_yeay	grandchild_to_grandparent	casual	field	harvest	I brought the extra hats. The ones on the cart were already soaked.
new_situation	worried	rith	sophea	friends_close	casual	field	harvest	The thresher belt is slipping. Don't feed another bundle until it sits tight.
new_situation	neutral	sophea	rith	friends_close	casual	field	harvest	I wedged a stick under the frame. The belt stopped walking off the pulley.
new_situation	happy	nita	lina	friends_close	casual	field	harvest	The sacks by the mango tree are full. We can mark those ones done.
new_situation	tired	lina	nita	friends_close	casual	field	harvest	I need ten minutes in the shade. My vision speckles when I stand fast.
new_situation	neutral	uncle_thon	nita	elder_to_youth	casual	field	harvest	Count the sacks out loud as they go on the cart. I lost one that way last season.
new_situation	worried	channary	uncle_thon	youth_to_elder	casual	field	harvest	The canal path is slick where the pump leaked. Carry the sack on the shoulder, not the hip.
new_situation	neutral	bopha	srey	friends_close	casual	field	harvest	I labeled this sack with charcoal. The blue string means it stays for seed.
new_situation	teasing	srey	bopha	friends_close	casual	field	harvest	You counted twelve and the cart has eleven. The missing one is behind your feet.
new_situation	neutral	vuthy	uncle_thon	youth_to_elder	casual	field	harvest	The scale at the mill opens at four. If we leave now the queue is short.
new_situation	worried	uncle_thon	vuthy	elder_to_youth	casual	field	harvest	Cover the grain with the plastic before we roll. Those clouds are not a maybe.
new_situation	happy	sophea	lina	friends_close	casual	field	harvest	The mill keeper waved us to the front. He remembered the seed sacks from June.
new_situation	worried	vuthy	mechanic_sam	customer_to_mechanic	casual	garage	moto_repair	The clutch lever sticks halfway. It started after the rainy ride back from the dock.
new_situation	neutral	mechanic_sam	vuthy	mechanic_to_customer	casual	garage	moto_repair	The cable is frayed inside the housing. A new lever will not fix that.
new_situation	neutral	sokha	mechanic_sam	customer_to_mechanic	casual	garage	moto_repair	Please check the front brake. It squeals only when I stop downhill.
new_situation	worried	mechanic_sam	sokha	mechanic_to_customer	casual	garage	moto_repair	The pad is down to metal. I will not send you out on that wheel.
new_situation	tired	rith	mechanic_sam	customer_to_mechanic	casual	garage	moto_repair	It dies at idle and catches if I blip the throttle. I need it for the night shift.
new_situation	neutral	mechanic_sam	rith	mechanic_to_customer	casual	garage	moto_repair	The spark plug is black and wet. I will dry the cap and try a spare.
new_situation	happy	lina	mechanic_sam	customer_to_mechanic	casual	garage	moto_repair	The headlight stays on now. Last night I was guessing the potholes.
new_situation	neutral	mechanic_sam	lina	mechanic_to_customer	casual	garage	moto_repair	I tightened the battery screws. They were loose enough to flicker on bumps.
new_situation	worried	dara	mechanic_sam	customer_to_mechanic	casual	garage	moto_repair	There is oil on the center stand. I don't know if it is the gasket or the chain lube.
new_situation	neutral	mechanic_sam	dara	mechanic_to_customer	casual	garage	moto_repair	The gasket weeps when the engine is hot. I can see the line under the cover.
new_situation	teasing	mechanic_sam	piseth	mechanic_to_customer	casual	garage	moto_repair	You rode here with the kickstand half down. I heard it before I saw you.
new_situation	neutral	piseth	mechanic_sam	customer_to_mechanic	casual	garage	moto_repair	The mirror cracked in a slow tip-over, not a crash. Can you swap just the glass?
new_situation	neutral	mechanic_sam	bopha	mechanic_to_customer	casual	garage	moto_repair	Leave the key. I will test the starter after lunch, when the bay is free.
new_situation	worried	bopha	mechanic_sam	customer_to_mechanic	casual	garage	moto_repair	The horn works only if I hit the housing. People behind me get no warning.
new_situation	happy	nita	mechanic_sam	customer_to_mechanic	casual	garage	moto_repair	Second gear engages without the grind. Whatever you adjusted, keep it.
new_situation	neutral	mechanic_sam	nita	mechanic_to_customer	casual	garage	moto_repair	I set the clutch free play to two fingers. Don't crank the adjuster on the ride back.
new_situation	worried	sopheak	mechanic_sam	customer_to_mechanic	casual	garage	moto_repair	The chain slaps the swingarm over every speed bump by the school wall.
new_situation	neutral	mechanic_sam	sopheak	mechanic_to_customer	casual	garage	moto_repair	It needs a link removed, not just oil. The slack is past the sticker mark.
new_situation	tender	channary	mechanic_sam	customer_to_mechanic	casual	garage	moto_repair	This bike is my father's. If a part is wrong, call me before you fit it.
new_situation	neutral	mechanic_sam	channary	mechanic_to_customer	casual	garage	moto_repair	I wrote the part number on the tag. Nothing gets bolted on until you nod.
new_situation	tired	visal	mechanic_sam	customer_to_mechanic	casual	garage	moto_repair	Can it wait until tomorrow? I only need the light and the brake for tonight's road.
new_situation	neutral	lina	tailor_mea	customer_to_tailor	casual	tailor	tailor	The sleeve catches when I lift a tray. Can you open the armhole a little?
new_situation	neutral	tailor_mea	lina	tailor_to_customer	casual	tailor	tailor	I will let out the seam under the arm. The cuff length can stay.
new_situation	worried	srey	tailor_mea	customer_to_tailor	casual	tailor	tailor	The school skirt twists after I sit. The waistband rides up on one side.
new_situation	neutral	tailor_mea	srey	tailor_to_customer	casual	tailor	tailor	The darts are uneven. Stand on the box and I will pin the higher hip.
new_situation	happy	channary	tailor_mea	customer_to_tailor	casual	tailor	tailor	The hem no longer brushes the wet step. You took exactly the finger I asked.
new_situation	neutral	tailor_mea	channary	tailor_to_customer	casual	tailor	tailor	I used the darker thread. The pale one would show on this cotton.
new_situation	worried	bopha	tailor_mea	customer_to_tailor	casual	tailor	tailor	The button loop is tight. My thumb can't get through it in a hurry.
new_situation	neutral	tailor_mea	bopha	tailor_to_customer	casual	tailor	tailor	I will recut the loop. Leave the blouse. It is a ten-minute job.
new_situation	tender	mother	tailor_mea	customer_to_tailor	casual	tailor	tailor	This shirt was his father's. Mend the elbow. Don't replace the cloth.
new_situation	neutral	tailor_mea	mother	tailor_to_customer	casual	tailor	tailor	I can patch from the inside with the spare from the hem. The pattern stays.
new_situation	neutral	dara	tailor_mea	customer_to_tailor	casual	tailor	tailor	The collar scratches my neck. Is that the new interfacing or a loose thread?
new_situation	neutral	tailor_mea	dara	tailor_to_customer	casual	tailor	tailor	A thread end. I will bury it. The interfacing is not against your skin.
new_situation	teasing	tailor_mea	rith	tailor_to_customer	casual	tailor	tailor	You breathed in when I measured and out when I cut. Pick one size.
new_situation	happy	rith	tailor_mea	customer_to_tailor	casual	tailor	tailor	The shoulders sit flat. Last uniform bunched when I carried the water bucket.
new_situation	worried	nita	tailor_mea	customer_to_tailor	casual	tailor	tailor	The zipper catches at the hip. I don't want it splitting during the ceremony.
new_situation	neutral	tailor_mea	nita	tailor_to_customer	casual	tailor	tailor	I will move the seam two centimeters. Come back before noon tomorrow to test the zip.
new_situation	neutral	sophea	tailor_mea	customer_to_tailor	casual	tailor	tailor	Please add a pocket that fits the phone. The current one swallows only a coin.
new_situation	neutral	tailor_mea	sophea	tailor_to_customer	casual	tailor	tailor	I can set a pocket in the side seam. It will not show under the vest.
new_situation	tired	vanna	tailor_mea	customer_to_tailor	casual	tailor	tailor	The costume cape is too long for the stage step. I tripped in rehearsal.
new_situation	neutral	tailor_mea	vanna	tailor_to_customer	casual	tailor	tailor	I will hem it to your ankle bone. Bring the shoes you actually wear on stage.
new_situation	happy	piseth	tailor_mea	customer_to_tailor	casual	tailor	tailor	The name-tag stitching is straight. Our boss notices crooked ones.
new_situation	worried	auntie_chenda	lina	elder_to_youth	casual	wedding_kitchen	wedding_kitchen	The banana-leaf plates are short by two stacks. Send someone to the stall before the guests sit.
new_situation	neutral	lina	auntie_chenda	youth_to_elder	casual	wedding_kitchen	wedding_kitchen	I counted the leaf stacks again. We are short only the dessert row.
new_situation	neutral	srey	auntie_chenda	youth_to_elder	casual	wedding_kitchen	wedding_kitchen	The soup is salted. I kept the chili in a separate bowl for the elders' table.
new_situation	worried	auntie_chenda	srey	elder_to_youth	casual	wedding_kitchen	wedding_kitchen	Stir the bottom of the beef pot. It caught once already on the left burner.
new_situation	happy	bopha	nita	friends_close	casual	wedding_kitchen	wedding_kitchen	The iced-coffee trays are full. Start them at the back table so the front stays clear.
new_situation	neutral	nita	bopha	friends_close	casual	wedding_kitchen	wedding_kitchen	I labeled the jugs. The white tape is sweet and the blue tape is plain.
new_situation	tired	vuthy	auntie_chenda	youth_to_elder	casual	wedding_kitchen	wedding_kitchen	The ice is melting in the tub. I can make one more run to the shop with the freezer.
new_situation	neutral	auntie_chenda	vuthy	elder_to_youth	casual	wedding_kitchen	wedding_kitchen	Go now. If you wait for the speeches, the ice will be water and a story.
new_situation	worried	channary	auntie_chenda	youth_to_elder	casual	wedding_kitchen	wedding_kitchen	A child licked the serving spoon and put it back. I pulled that spoon out.
new_situation	neutral	auntie_chenda	channary	elder_to_youth	casual	wedding_kitchen	wedding_kitchen	Good. Wash it at the outdoor tap. Don't dry it on the guest towels.
new_situation	teasing	rith	sophea	friends_close	casual	wedding_kitchen	wedding_kitchen	You have been tasting the curry so carefully that the pot knows your name.
new_situation	neutral	sophea	rith	friends_close	casual	wedding_kitchen	wedding_kitchen	I tasted once, with a clean spoon. The pot is still for the guests.
new_situation	neutral	piseth	auntie_chenda	youth_to_elder	casual	wedding_kitchen	wedding_kitchen	The gas cylinder hissed when I switched it. The new one is the blue valve.
new_situation	worried	auntie_chenda	piseth	elder_to_youth	casual	wedding_kitchen	wedding_kitchen	Leave the old cylinder upright outside. Don't roll it toward the charcoal.
new_situation	happy	dara	lina	friends_close	casual	wedding_kitchen	wedding_kitchen	The fruit platters match. I put the mango on the left of every tray.
new_situation	neutral	grandma_yeay	auntie_chenda	elder_to_elder	casual	wedding_kitchen	wedding_kitchen	Save a plate for the musicians. They eat after the first song, not with the hall.
new_situation	tender	auntie_chenda	vanna	elder_to_youth	casual	wedding_kitchen	wedding_kitchen	You can carry the napkins, not the soup. Both hands, and watch the step at the tent.
new_situation	neutral	vanna	srey	friends_close	casual	wedding_kitchen	wedding_kitchen	The napkins are on the side table. I left the extra bundle under the pink cloth.
new_situation	worried	sokha	auntie_chenda	youth_to_elder	casual	wedding_kitchen	wedding_kitchen	The rain is hitting the tent seam above the rice. I moved the pot one table over.
new_situation	neutral	auntie_chenda	sokha	elder_to_youth	casual	wedding_kitchen	wedding_kitchen	Put the plastic sheet on the seam, not on the food. Ask Visal to hold the pole.
new_situation	happy	nita	auntie_chenda	youth_to_elder	casual	wedding_kitchen	wedding_kitchen	The couple's table has the small bowls. I kept the chili jar off that one.
new_situation	neutral	librarian_keo	dara	librarian_to_student	formal	library	library	Whisper if you must talk. The exam readers are along the window side.
new_situation	worried	dara	librarian_keo	student_to_librarian	formal	library	library	The page I need is torn out of the atlas. Is there a second copy in the back room?
new_situation	neutral	librarian_keo	dara	librarian_to_student	formal	library	library	The second atlas is on the reserve shelf. You can read it here. It does not leave.
new_situation	neutral	srey	librarian_keo	student_to_librarian	formal	library	library	My card is at home. Can you look me up by the class list instead?
new_situation	neutral	librarian_keo	srey	librarian_to_student	formal	library	library	I found your name. Two books are already out. This one makes three, which is the limit.
new_situation	worried	lina	nita	friends_close	casual	library	library	Don't highlight that. It belongs to the shelf, not to your notes.
new_situation	neutral	nita	lina	friends_close	casual	library	library	I was using a pencil tick in my own notebook. The book stays clean.
new_situation	tired	rith	librarian_keo	student_to_librarian	formal	library	library	May I stay until you lock the gate? The chapter ends in six pages.
new_situation	neutral	librarian_keo	rith	librarian_to_student	formal	library	library	You may stay until the bell I ring at six. After that the lights go off with me.
new_situation	happy	bopha	srey	friends_close	casual	library	library	I found the folk-tale index. The story you wanted is under the river section.
new_situation	neutral	piseth	librarian_keo	student_to_librarian	formal	library	library	The fan on this desk rattles. May I move to the empty table by the dictionaries?
new_situation	neutral	librarian_keo	piseth	librarian_to_student	formal	library	library	Take the table. Leave the dictionary volumes standing. They lose pages if they lie flat.
new_situation	worried	vanna	librarian_keo	student_to_librarian	formal	library	library	I spilled a drop of water on the cover, not the pages. I blotted it with my sleeve.
new_situation	neutral	librarian_keo	vanna	librarian_to_student	formal	library	library	Show me the cover. If the board warped, we note it. Don't try to dry it in the sun.
new_situation	teasing	sophea	dara	friends_close	casual	library	library	You have been on the same paragraph since the clock jumped. The paragraph is winning.
new_situation	neutral	channary	librarian_keo	student_to_librarian	formal	library	library	Is the oral-history shelf the low one? I need the interview about the old market fire.
new_situation	neutral	librarian_keo	channary	librarian_to_student	formal	library	library	The market-fire tapes are in the gray box, reel three. Headphones are in the drawer under the counter.
new_situation	worried	sokha	librarian_keo	student_to_librarian	formal	library	library	Someone left a phone charging in the outlet by the plants. It is not mine.
new_situation	neutral	librarian_keo	sokha	librarian_to_student	formal	library	library	I will unplug it and keep it at the desk. Tell your class to claim it before closing.
new_situation	happy	nita	librarian_keo	student_to_librarian	formal	library	library	The book I reserved is actually here. I expected another week of the waiting list.
new_situation	tender	librarian_keo	nita	librarian_to_student	formal	library	library	It came back this morning. I set it aside with your name on a paper strip.
new_situation	worried	visal	printer_sok	customer_to_printer	casual	print_shop	print_shop	The poster colors shifted to pink. The logo is supposed to be the dark red.
new_situation	neutral	printer_sok	visal	printer_to_customer	casual	print_shop	print_shop	The magenta ran high. I will reprint from the file, not from the pink copy.
new_situation	neutral	sophea	printer_sok	customer_to_printer	casual	print_shop	print_shop	I need forty forms, single sided, before the office opens at eight.
new_situation	worried	printer_sok	sophea	printer_to_customer	casual	print_shop	print_shop	The cutter jammed on the last stack. I can finish twenty now and the rest by seven.
new_situation	happy	lina	printer_sok	customer_to_printer	casual	print_shop	print_shop	The invitation text fits the card. You caught the date I had typed wrong.
new_situation	neutral	printer_sok	lina	printer_to_customer	casual	print_shop	print_shop	I changed only the date line. Read it once more before I run the hundred.
new_situation	worried	dara	printer_sok	customer_to_printer	casual	print_shop	print_shop	The power dipped and the printer ate the page. Is my file still in the queue?
new_situation	neutral	printer_sok	dara	printer_to_customer	casual	print_shop	print_shop	The file is on the stick, not in the machine. The machine forgets when the lights blink.
new_situation	neutral	srey	printer_sok	customer_to_printer	casual	print_shop	print_shop	Please bind these on the left. The teacher marks the right margin.
new_situation	teasing	printer_sok	rith	printer_to_customer	casual	print_shop	print_shop	You asked for color and then gasped at the price. Black ink is still legal.
new_situation	neutral	rith	printer_sok	customer_to_printer	casual	print_shop	print_shop	Black is fine for the draft. Color only the cover sheet with the diagram.
new_situation	worried	bopha	printer_sok	customer_to_printer	casual	print_shop	print_shop	The laminate is bubbling on the corner. I have to show this identity copy today.
new_situation	neutral	printer_sok	bopha	printer_to_customer	casual	print_shop	print_shop	I will run a new sleeve. Don't peel the bubbled one or the toner lifts with it.
new_situation	tired	nita	printer_sok	customer_to_printer	casual	print_shop	print_shop	Can you scan both sides into one file? The office will not take two attachments.
new_situation	neutral	printer_sok	nita	printer_to_customer	casual	print_shop	print_shop	One file, two pages. I will name it with today's date so you can find it.
new_situation	happy	channary	printer_sok	customer_to_printer	casual	print_shop	print_shop	The staples are even. The last shop put them through the page numbers.
new_situation	neutral	piseth	printer_sok	customer_to_printer	casual	print_shop	print_shop	The receipt text is faint. Can you darken the copy without enlarging it?
new_situation	neutral	printer_sok	piseth	printer_to_customer	casual	print_shop	print_shop	I will raise the density one step. If I go further the background turns gray.
new_situation	worried	sokha	printer_sok	customer_to_printer	casual	print_shop	print_shop	Don't leave my certificate on the counter. Names on that page are enough for a stranger.
new_situation	neutral	printer_sok	sokha	printer_to_customer	casual	print_shop	print_shop	It stays behind the desk until you pay. I don't display certificates.
new_situation	tender	vanna	printer_sok	customer_to_printer	casual	print_shop	print_shop	This drawing is for my grandmother. Please don't crop the house in the corner.
new_situation	worried	kosal	sopheak	neighbor_to_neighbor	casual	rooftop	rooftop_tank	The tank is overflowing down my wall. Your float valve didn't stop.
new_situation	neutral	sopheak	kosal	neighbor_to_neighbor	casual	rooftop	rooftop_tank	I shut the inlet. The valve sticks when the lid grit sits in the hinge.
new_situation	worried	lina	father	child_to_parent	casual	rooftop	rooftop_tank	Dad, the ladder to the tank shakes on the third rung. I didn't climb past it.
new_situation	neutral	father	lina	parent_to_child	casual	rooftop	rooftop_tank	Good that you stopped. I will replace that rung before anyone goes up again.
new_situation	neutral	vuthy	kosal	neighbor_to_neighbor	casual	rooftop	rooftop_tank	I can hear the pump short-cycling. It kicks on every few minutes and the pipes knock.
new_situation	worried	kosal	vuthy	neighbor_to_neighbor	casual	rooftop	rooftop_tank	Don't open the pump cover while it is kicking. I will pull the breaker first.
new_situation	happy	srey	mother	child_to_parent	casual	rooftop	rooftop_tank	Mom, the tank lid is latched. I checked the mosquito screen is tucked under the rim.
new_situation	tender	mother	srey	parent_to_child	casual	rooftop	rooftop_tank	Thank you. Leave the screen. If you rinse it, put it back before dusk.
new_situation	neutral	piseth	sopheak	neighbor_to_neighbor	casual	rooftop	rooftop_tank	There is algae on the overflow. I am not drinking from the tap until the tank is drained.
new_situation	neutral	sopheak	piseth	neighbor_to_neighbor	casual	rooftop	rooftop_tank	We drain on Sunday morning. Bring a bucket if you want the first clean water for washing.
new_situation	worried	nita	father	child_to_parent	casual	rooftop	rooftop_tank	Dad, a bird is trapped under the tank lid. I can hear it, I can't see it.
new_situation	neutral	father	nita	parent_to_child	casual	rooftop	rooftop_tank	I will lift the lid from the hinge side. You stand back in case it flies at our faces.
new_situation	tired	dara	kosal	neighbor_to_neighbor	casual	rooftop	rooftop_tank	The shared hose is cracked at the roof joint. Water sprays the hot tin and disappears.
new_situation	neutral	kosal	dara	neighbor_to_neighbor	casual	rooftop	rooftop_tank	I have a coupling in the tool tin. We can cut the cracked span and join it.
new_situation	teasing	rith	sopheak	neighbor_to_neighbor	casual	rooftop	rooftop_tank	You blamed my laundry for the low pressure. Your valve was the one left open.
new_situation	neutral	bopha	mother	child_to_parent	casual	rooftop	rooftop_tank	Mom, the roof door sticks. I had to shoulder it, and the bolt is bent.
new_situation	worried	mother	bopha	parent_to_child	casual	rooftop	rooftop_tank	Don't shoulder it again. If the bolt shears, the door swings over the drop.
new_situation	happy	channary	lina	friends_close	casual	rooftop	rooftop_tank	The new float shuts off clean. I watched the waterline stop below the overflow hole.
new_situation	neutral	visal	kosal	neighbor_to_neighbor	casual	rooftop	rooftop_tank	I labeled the breaker for the pump. It was unmarked and I almost cut the hallway lights.
new_situation	worried	sokha	sopheak	neighbor_to_neighbor	casual	rooftop	rooftop_tank	The tank stand rocks when the pump starts. One foot is on a cracked tile.
new_situation	neutral	sopheak	sokha	neighbor_to_neighbor	casual	rooftop	rooftop_tank	I will wedge a flat steel plate under that foot today. Don't store buckets against the leg.
new_situation	neutral	coach_sen	srey	coach_to_player	casual	court	volleyball	Serve from behind the line. Your toe was on it for the last two points.
new_situation	worried	srey	coach_sen	player_to_coach	casual	court	volleyball	The net post leans after the rain. The tape measure says it is low on the left.
new_situation	neutral	coach_sen	dara	coach_to_player	casual	court	volleyball	Call the ball. Two of you went up and nobody's arms were ready underneath.
new_situation	happy	dara	rith	friends_close	casual	court	volleyball	Your set finally sat high enough. I didn't have to swing from my knees.
new_situation	teasing	rith	dara	friends_close	casual	court	volleyball	You swung anyway and the ball visited the noodle stall. Go ask for it nicely.
new_situation	tired	lina	coach_sen	player_to_coach	casual	court	volleyball	My shoulder clicks on the float serve. Can I switch to setting this game?
new_situation	neutral	coach_sen	lina	coach_to_player	casual	court	volleyball	Set this game. If the click gets sharper, you sit, even if we are short.
new_situation	worried	nita	bopha	friends_close	casual	court	volleyball	The court paint is slick by the center line. I almost lost my footing on the block.
new_situation	neutral	bopha	nita	friends_close	casual	court	volleyball	I saw it. We wipe with the dry towel, not the water bottle. Water makes it worse.
new_situation	happy	piseth	coach_sen	player_to_coach	casual	court	volleyball	We rotated without a gap. The new kid knew when to move to serve.
new_situation	neutral	coach_sen	piseth	coach_to_player	casual	court	volleyball	Keep that talk on court. Point at the spot, don't narrate the last mistake.
new_situation	worried	vanna	coach_sen	player_to_coach	casual	court	volleyball	The ball has a soft panel. It wobbles when I float it.
new_situation	neutral	coach_sen	vanna	coach_to_player	casual	court	volleyball	Use the spare ball with the black valve. Leave the soft one for warmups.
new_situation	tender	channary	srey	friends_close	casual	court	volleyball	Ice that wrist before you cycle home. You landed on it and kept playing.
new_situation	neutral	sophea	coach_sen	player_to_coach	casual	court	volleyball	The lights hum and then dim. If they drop again we should stop. The lines disappear.
new_situation	worried	coach_sen	sophea	coach_to_player	casual	court	volleyball	Agreed. One more dim and we quit. I am not calling lines we cannot see.
new_situation	teasing	sokha	rith	friends_close	casual	court	volleyball	You celebrated a point that was still on our side of the net. Impressive confidence.
new_situation	neutral	vuthy	coach_sen	player_to_coach	casual	court	volleyball	May I tape my fingers? The set keeps hitting the nail and it splits.
new_situation	neutral	coach_sen	vuthy	coach_to_player	casual	court	volleyball	Tape them. Keep the tape off the palm or you will lose the grip when you sweat.
new_situation	happy	bopha	lina	friends_close	casual	court	volleyball	The scoreboard chalk survived the drizzle. We don't have to argue the number.
new_situation	tired	dara	coach_sen	player_to_coach	casual	court	volleyball	I can play the next set or I can keep score. I can't jump and write.
""".strip()


def _norm(text: str) -> str:
    cleaned = text.lower().replace("'", "'")
    cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _content(text: str) -> set[str]:
    return {word for word in _norm(text).split() if word not in STOP and len(word) > 2}


def _grams(text: str) -> set[tuple[str, ...]]:
    words = _norm(text).split()
    found = set()
    for index in range(len(words) - 4):
        gram = tuple(words[index:index + 5])
        if sum(1 for word in gram if word not in STOP and len(word) > 2) >= 3:
            found.add(gram)
    return found


def _parse() -> list[dict]:
    rows = []
    for line_no, line in enumerate(RAW.splitlines(), start=1):
        parts = line.split("\t")
        if len(parts) != 9:
            raise SystemExit(f"line {line_no} has {len(parts)} fields")
        kind, emotion, speaker, listener, relationship, register, setting, category, text = parts
        text = text.strip()
        if kind not in {"bank_leftover", "new_situation"}:
            raise SystemExit(f"bad kind on line {line_no}")
        if emotion not in {"formal", "teasing", "worried", "neutral", "happy", "sad", "tired", "afraid", "tender", "angry"}:
            raise SystemExit(f"bad emotion {emotion}")
        rows.append({
            "kind": kind,
            "emotion": emotion,
            "speaker_id": speaker,
            "listener_id": listener,
            "relationship": relationship,
            "register": register,
            "setting": setting,
            "category": category,
            "source_text": text,
        })
    return rows


def _reject(drafts: list[dict], existing_norms: set[str], existing_content: list[set[str]], existing_grams: set[tuple[str, ...]]) -> list[str]:
    problems: list[str] = []
    seen: set[str] = set()
    seen_grams: set[tuple[str, ...]] = set()
    openings = Counter()
    for index, draft in enumerate(drafts, start=1):
        text = draft["source_text"]
        words = text.split()
        key = _norm(text)
        if not 6 <= len(words) <= 22:
            problems.append(f"{index} length {len(words)}: {text}")
        if not key or key in existing_norms or key in seen:
            problems.append(f"{index} exact duplicate: {text}")
        seen.add(key)
        content = _content(text)
        if len(content) >= 4:
            for other in existing_content:
                if not other:
                    continue
                score = len(content & other) / len(content | other)
                if score >= 0.42:
                    problems.append(f"{index} jaccard {score:.2f}: {text}")
                    break
        grams = _grams(text)
        hit = grams & existing_grams
        if hit:
            problems.append(f"{index} shared 5-gram {next(iter(hit))}: {text}")
        inner = grams & seen_grams
        if inner:
            problems.append(f"{index} shared new 5-gram {next(iter(inner))}: {text}")
        seen_grams |= grams
        openings[" ".join(_norm(text).split()[:4])] += 1
    for opening, count in openings.items():
        if count >= 8:
            problems.append(f"opening used {count} times: {opening}")
    return problems


def _row(number: int, draft: dict) -> dict:
    return {
        "id": f"kp-{number:04d}",
        "source_text": draft["source_text"],
        "source_lang": "en",
        "target_lang": "km",
        "stub_khmer": "",
        "candidates": [],
        "approved_text": "",
        "speaker_id": draft["speaker_id"],
        "listener_id": draft["listener_id"],
        "relationship": draft["relationship"],
        "emotion": draft["emotion"],
        "register": draft["register"],
        "category": draft["category"],
        "origin": "synthetic",
        "license_type": "unknown",
        "license_notes": LICENSE_NOTES,
        "review_status": "pending_native_review",
        "verified_by": "",
        "verified_at": "",
        "reviewer_notes": REVIEWER_NOTES,
        "metadata": {
            "provenance": "synthetic_draft",
            "synthetic_draft": True,
            "source_file": "data/khmer_spoken/workspace/spoken_train_next.jsonl",
            "licence": None,
            "not_for_gold": True,
            "not_for_weight_training": True,
            "locked_from_training": False,
            "scale_pool": "train_next",
            "setting": draft["setting"],
            "expansion": "kp-2001-kp-2200",
            "created_on": "2026-10-26",
            "situation_kind": draft["kind"],
            "holdout": False,
            "note": (
                "Synthetic draft. Distinct from kp-001 through kp-2000. "
                "Licence unknown. Not gold. Not a weight update."
            ),
        },
        "schema_version": SCHEMA_VERSION,
    }


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    before = hashlib.sha256(SCALE.read_bytes()).hexdigest()
    scale_rows = [json.loads(line) for line in SCALE.read_text(encoding="utf-8").splitlines() if line.strip()]
    if [row["id"] for row in scale_rows] != [f"kp-{index:03d}" for index in range(1, 2001)]:
        raise SystemExit("spoken_scale ids are not kp-001 through kp-2000")
    holdout_filled = 0
    for row in scale_rows:
        number = int(row["id"].split("-")[1])
        if 1001 <= number <= 2000 and any(str((cand or {}).get("text") or "").strip() for cand in (row.get("candidates") or [])):
            holdout_filled += 1
    existing_norms = {_norm(row["source_text"]) for row in scale_rows}
    existing_content = [_content(row["source_text"]) for row in scale_rows]
    existing_grams: set[tuple[str, ...]] = set()
    for row in scale_rows:
        existing_grams |= _grams(row["source_text"])
    drafts = _parse()
    if len(drafts) != 200:
        raise SystemExit(f"expected 200 drafts, got {len(drafts)}")
    problems = _reject(drafts, existing_norms, existing_content, existing_grams)
    if problems:
        print(f"REJECT {len(problems)}")
        for item in problems[:40]:
            print(item)
        raise SystemExit("new rows are not distinct enough")
    built = [_row(2000 + index, draft) for index, draft in enumerate(drafts, start=1)]
    if [row["id"] for row in built] != [f"kp-{index:04d}" for index in range(2001, 2201)]:
        raise SystemExit("ids are not kp-2001 through kp-2200")
    for row in built:
        if row["origin"] in {"human_authored", "human_reviewed", "human", "gold"}:
            raise SystemExit(f"{row['id']} origin is forbidden")
        if row["review_status"] != "pending_native_review" or row["license_type"] != "unknown":
            raise SystemExit(f"{row['id']} review or licence is wrong")
        if row["verified_by"] or row["approved_text"] or row["candidates"]:
            raise SystemExit(f"{row['id']} looks approved or filled")
        number = int(row["id"].split("-")[1])
        if 1001 <= number <= 2000:
            raise SystemExit("holdout id in the new file")
    lines = [json.dumps(row, ensure_ascii=False) for row in built]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(OUT.suffix + ".tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(tmp, OUT)
    after = hashlib.sha256(SCALE.read_bytes()).hexdigest()
    if after != before:
        raise SystemExit("spoken_scale.jsonl changed during the write")
    kinds = Counter(draft["kind"] for draft in drafts)
    print(
        json.dumps({
            "wrote": str(OUT.relative_to(ROOT)),
            "rows": len(built),
            "id_first": built[0]["id"],
            "id_last": built[-1]["id"],
            "kinds": dict(kinds),
            "licence": "unknown",
            "review_status": "pending_native_review",
            "origin": "synthetic",
            "holdout_filled_on_scale": holdout_filled,
            "scale_sha256_unchanged": after,
            "weights_started": False,
        }, ensure_ascii=False),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
