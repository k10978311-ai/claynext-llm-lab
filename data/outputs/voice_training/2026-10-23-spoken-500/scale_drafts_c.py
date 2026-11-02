"""Original synthetic lines, groups 11–15, plus top-ups. Not commercial dialogue."""
from __future__ import annotations

SCHOOL = """
neutral|Teacher, may I go to the toilet before the next exercise?
formal|Open your book to the page I wrote on the board.
neutral|I don't understand the second line. Can you say it slower?
formal|Hand in the sheet even if one answer is blank.
worried|Teacher, my stomach hurts. May I sit near the door?
neutral|Don't copy his paper. Write what you actually think.
formal|We will read aloud one by one. Listen for your name.
neutral|I left my ruler at home. May I borrow one for this class?
formal|The test is tomorrow. Review the words on the back page.
neutral|Teacher, the fan is hitting the paper off my desk.
worried|I missed yesterday. Which exercise should I do first?
neutral|Please speak so the back row can hear the example.
formal|Group three, your poster is due before the bell, not after.
neutral|May I sharpen my pencil? The point broke on the last sum.
formal|Don't shout the answer. Raise your hand and wait.
neutral|Teacher, the board light is reflecting and I can't see the chart.
worried|Someone took my notebook from the shelf. It has a red cover.
neutral|Write the date at the top. Several of you skipped it.
formal|If you finish early, read quietly. Don't walk around.
neutral|Teacher, can you check this sentence before I copy it into the book?
formal|We are not using phones in this period. Put them in the bag.
neutral|I studied the wrong chapter. Is the quiz still on chapter four?
worried|Teacher, the boy behind me keeps tapping my chair.
neutral|Say the word, then use it in a short spoken line.
formal|Partners, switch papers and circle only the spelling.
neutral|May I sit closer? I can't hear when the rain hits the roof.
formal|The homework is to ask a family member one question and write the answer.
neutral|Teacher, I already handed mine in. It's under the blue folder.
worried|My pen leaked on the sheet. May I have another page?
neutral|Don't laugh when someone misreads. You will read next.
formal|Today we practice polite requests. Start with a real classroom need.
neutral|Teacher, the clock is wrong. The bell already rang in the other building.
formal|Leave the dictionaries on the desk. You'll need them in a minute.
neutral|I can read it, but I don't know how to say the second word.
worried|Teacher, I feel dizzy. Can I put my head down for a minute?
neutral|Write larger. I can't mark what I can't read.
formal|The group by the window, turn your chairs back toward the board.
neutral|May I drink water? I won't walk around with the bottle.
formal|If you were absent, copy the board notes from a classmate tonight.
neutral|Teacher, is this answer too short or is the idea enough?
formal|We stop when I raise my hand, even if you are mid-sentence.
neutral|I forgot the homework sheet at home. I can bring it after lunch.
worried|Teacher, two answers got erased when a hand crossed my page.
neutral|Read the question twice before you pick. The last word changes it.
formal|No one leaves until the rows are straight and the floor is clear.
neutral|Teacher, may I explain it in a sentence instead of the formula?
formal|The oral practice is in pairs. Face each other, not the board.
neutral|I know the story but not the spelling of the names.
worried|Teacher, the door keeps opening and the pages blow.
neutral|Please collect the scissors by counting them back to twenty.
formal|Tomorrow, bring a short memory from home. Two or three spoken lines.
neutral|Teacher, can we do the example together once more?
formal|If you don't know, say "I'm not sure" instead of guessing a joke.
neutral|My partner is absent. May I join the pair by the wall?
worried|Teacher, I have a nosebleed. May I go to the washroom?
neutral|Underline the word you want me to hear when you read aloud.
formal|The quiz is ten minutes. I will not repeat the prompt.
neutral|Teacher, I finished. Should I draw a line under the last answer?
formal|Stack the books by size so the cupboard door can close.
neutral|I mixed up the two similar words. Can you say them one after another?
worried|Teacher, the bench is broken on this end. Can I move?
neutral|Write your name before you write anything else. Blank names don't get marks.
formal|We will stop five minutes early to hear three volunteers.
neutral|Teacher, is the homework the dialogue or the word list?
formal|Keep your voice at a speaking level. This is not the yard.
neutral|I can say it to you quietly first. I'm not ready for the class.
worried|Teacher, my eyes hurt from the board. May I copy from her notebook?
neutral|Don't rock the chair. The bolt is already loose.
formal|Today's line to practice at home is the one I starred.
neutral|Teacher, we ran out of chalk in this room. The box is empty.
formal|Hand the sheets forward. Don't pass them to the side.
neutral|I understood the story and missed the question's last part.
worried|Teacher, someone wrote on my cover. It wasn't me.
neutral|Please repeat the polite form. I keep starting with the short one.
formal|Sit down when you finish speaking. Don't stay standing at the desk.
neutral|Teacher, may I open the window a little? The room is heavy.
formal|The mark is for a clear sentence, not for the longest one.
neutral|I'll try again. The first try used the wrong address word.
worried|Teacher, the rain is coming onto the last desk. Can we shift it?
neutral|Collect the pencils that belong to the class, not your own.
formal|If you need to leave early, bring a note. Don't just stand up.
neutral|Teacher, can you listen to my line before the bell?
formal|That is enough practice for today. Put the books away quietly.
happy|Teacher, I remembered the line on the way up to the board.
neutral|Write what you would actually say, not a proverb you memorized.
formal|The next class needs this room. Leave it as you found it.
worried|Teacher, I don't have the book yet. My brother has it this morning.
neutral|May I answer in two sentences? One feels too small for the question.
formal|Look at the listener when you speak. The board is not the listener.
neutral|Teacher, I think I swapped the names. Can I read it once more?
formal|Good. That was a real request, not a command. Next pair.
neutral|I left my water bottle in the other room. May I get it at the break?
worried|Teacher, the group is arguing about the answer. Can you listen?
neutral|I'll write the correction in the margin so I can see the old mistake.
formal|Pack up only when I say so. The bell is a reminder, not the instruction.
neutral|Teacher, thank you. I can say it without looking now.
formal|Tomorrow we start with yesterday's line. Don't lose the paper.
neutral|My voice is quiet. Tell me if the back row can't hear.
worried|Teacher, I need to call home at the break. My mother asked me to.
neutral|The example on the board uses a different address. Should we copy that one?
formal|You may use the dictionary for spelling and not for the whole sentence.
neutral|Teacher, I'll bring the signed page tomorrow morning, before class.
formal|That ends the speaking practice. Hands down. Eyes here.
""".strip().splitlines()

CLINIC = """
worried|Doctor, the cough is worse when I lie on my left side.
formal|When did the fever start, and did you take anything for it?
worried|I can still walk. I just can't put the heel down.
formal|Breathe in through your nose and out slowly. Again.
worried|The pain is here, under the ribs, after I eat greasy food.
formal|I need to see the other ear as well. Turn a little.
worried|My child hasn't kept water down since last night.
formal|This is not an emergency, but don't wait a week. Come back in two days.
worried|The cut is small and it won't stop bleeding when I wash.
formal|Keep the bandage dry. If the redness spreads, return the same day.
worried|I get dizzy when I stand up fast in the morning.
formal|Are you taking the tablets with food, or on an empty stomach?
worried|My throat is sharp on one side. Swallowing hurts.
formal|I'm going to press your stomach. Tell me when it hurts, not before.
worried|The rash started after the new soap. It itches at night.
formal|Don't scratch. I'll give you something for the itch, not for the cause yet.
worried|I twisted the wrist catching a falling pot. It swelled by evening.
formal|Move the fingers. Good. Now don't lift with that hand for three days.
worried|The headache sits behind the eyes after I read at night.
formal|Sleep and water first. Come back if you vomit or the pain wakes you.
worried|My mother is weaker today. She didn't finish the porridge.
formal|Has she been coughing, or is it only the fatigue?
worried|The burn is from the kettle. I ran water on it already.
formal|Don't put paste on it. Keep it clean and covered.
worried|I can't sleep because the ankle throbs when the fan hits it.
formal|Raise it on a cushion tonight. If it's hot and tight tomorrow, come in.
worried|The child has a rash and a fever together. I'm frightened.
formal|We'll check the temperature now. When did the rash appear?
worried|I feel short of breath on the stairs, not on flat ground.
formal|Sit and breathe. I'm going to listen to your chest. Don't talk for a moment.
worried|The toothache kept me up. The gum is swollen on the left.
formal|I can give you something for the pain. You still need a dentist this week.
worried|I skipped two doses because the tablets made me nauseous.
formal|Don't stop the course without telling me. We'll adjust the timing.
worried|My eye is red and sticky in the morning. The other eye is fine.
formal|Don't share the towel. Wash your hands before you touch the good eye.
worried|The diarrhea started after the street noodles yesterday.
formal|Sip the salt water I wrote down. If there's blood, come back tonight.
worried|I have a lump under the arm that wasn't there last month.
formal|We'll note the size. Don't poke it. Come back if it grows or hurts.
worried|The old cut reopened when I carried the rice sack.
formal|I'll clean it. Tell me if the numbness in the finger is new.
worried|My father won't come himself. He asked me to describe the chest pain.
formal|Chest pain needs him here, not a description. Can you bring him today?
worried|The medicine tastes bitter and the child spits it out.
formal|Mix it with a spoon of something he likes, and give the full spoon.
worried|I feel tingling in two fingers after hours on the motorbike.
formal|Rest the wrist at night. If the tingling climbs the arm, come back.
worried|The period is heavier than usual and I'm dizzy when I stand.
formal|Sit down. I'll check your pulse. Tell me how many days this has lasted.
worried|A dog scratched my leg. The skin broke. The dog is the neighbor's.
formal|Wash it again at home. We should talk about the dog's vaccines today.
worried|The inhaler is empty and the night air makes me wheeze.
formal|Use the spare if you have it. I'll write the refill. Don't wait until midnight.
worried|I hit my head on the cupboard. I didn't black out. I have a lump.
formal|Watch for vomiting or confusion tonight. Wake him once and ask his name.
worried|The joint clicks and then locks. I have to shake it loose.
formal|Don't force it. We'll try a wrap. Avoid squatting for a few days.
worried|I think the fever broke, but I'm sweating and cold together.
formal|That's common. Keep drinking. If it spikes again, you already know the dose.
worried|The baby is tugging one ear and cried all evening.
formal|I'll look in the ear. Hold his head gently against your chest.
worried|My back seized when I lifted the water jug. I can't stand straight.
formal|Lie on your side for the exam. We'll talk about how you lift after.
worried|The tablets helped the pain and upset my stomach.
formal|Take them after a meal from now on. Tell me if the pain is still there Friday.
worried|I have white spots in my mouth and it hurts to eat chili.
formal|Skip the chili. I'll look with the light. This may be simple irritation.
worried|The stitch from last month is red at one end.
formal|Is there pus, or only redness? Don't pull the stitch yourself.
worried|I fainted in the heat at the market and someone sat me down.
formal|Did you eat before you went out? Heat plus an empty stomach does this.
worried|The urine burns. I drank a lot of water and it still burns.
formal|We'll test it. Finish the sample cup and leave it in the window box.
worried|My knee is hot after the fall, and I don't trust it on the stairs.
formal|Use the rail. If it gives way under you, stop and come back the same day.
worried|The cough brings up pale phlegm in the morning only.
formal|Any blood, even a streak, you come back. Otherwise try the steam I described.
worried|I am afraid of the injection. The last one made my arm heavy.
formal|We'll use the smaller needle. Look at the poster, not at your arm.
worried|The child ate a coin. He is breathing normally and crying loudly.
formal|Don't try to make him vomit. If he drools or can't swallow, we go further tonight.
worried|I have a ringing in one ear since the firecrackers.
formal|It may fade. If it's still there in three days, or if you feel off balance, return.
worried|The wound from the coral is itchy and tight.
formal|Salt water rinses, not perfume or paste. Cover it when you go out in the dust.
worried|I keep waking at three with my heart racing, then it settles.
formal|Write down what you ate and whether you were dreaming. Bring the note next time.
worried|Doctor, I can pay today. I don't want to owe the clinic.
formal|We'll do what is needed first. The desk will tell you the number after.
neutral|The line is long. I'll wait. Please see the baby before me.
formal|Nurse, he hasn't had water in an hour. Can someone look soon?
worried|I lost the paper with the dose. I remember two tablets, not the hours.
formal|Don't guess the hours. I'll rewrite it. Bring the box next visit.
neutral|The pharmacy downstairs is closed. Is there another place for this tonight?
formal|Yes. I'll mark the paper. Don't substitute a different strength.
worried|My hands shake when I hold the cup. It started this month.
formal|Hold both hands out. Good. Any new medicine in that month?
worried|The blister popped on its own. The skin underneath is very pink.
formal|Leave it open to the air at home and covered if you go to the market.
worried|I am pregnant and the smell of frying makes me retch. Is that dangerous?
formal|Small meals help. Come back if you can't keep water down for half a day.
worried|The cramp is in the calf at night, after I stand at the stall all day.
formal|Stretch before sleep. If the leg swells or goes red, that is a different visit.
worried|Doctor, speak a little slower. I want to repeat the instructions back.
formal|Good. Say them back now. I'll correct only the part about the timing.
neutral|Thank you. I'll bring my father tomorrow morning, before the rush.
formal|Come early. If the chest pain returns tonight, don't wait for morning.
""".strip().splitlines()

PAGODA = """
neutral|Venerable, we brought rice and fruit for the morning offering.
formal|Leave your shoes on the lower step, and wash your hands first.
neutral|Venerable, may I ask which day the ceremony begins?
formal|Come after the morning chant, not during it.
neutral|Venerable, please remember my mother. She is ill at home.
formal|Sit quietly. If the child cries, take him outside and return.
neutral|Venerable, the shoes are in a row, as you asked last week.
formal|Do not step over the offering trays. Walk behind them.
neutral|Venerable, may I sweep the yard before people arrive?
formal|The broom is by the drum room. Sweep away from the hall.
neutral|Venerable, I don't know the response. May I listen this time?
formal|Listening is enough today. Don't pretend the words you don't have.
neutral|Venerable, we brought water for the visitors. Where should it stand?
formal|In the shade, not in the doorway. People need the path clear.
neutral|Venerable, my father asked me to apologize for missing the last ceremony.
formal|Tell him he is welcome on the next holy day. Don't promise for him.
neutral|Venerable, may the children sit at the back if they can't stay still?
formal|Yes. If they run, a parent goes with them. The hall is not a yard.
neutral|Venerable, I cleaned the bowls and stacked them by size.
formal|Good. Cover them. Flies are already in the sun.
neutral|Venerable, is it all right if I leave before the meal? I have a shift.
formal|Leave quietly by the side. Don't cross in front of people who are seated.
neutral|Venerable, the microphone cuts out on the second word.
formal|Then we will not use it. A loud voice is enough for this yard.
neutral|Venerable, I brought a new mat. The old one tore at the corner.
formal|Lay it where the sun can dry the floor first.
neutral|Venerable, may I ask you to speak with my brother? He is angry at home.
formal|I can listen. I will not take a side you haven't told him about.
neutral|Venerable, the incense is strong. Should I open the side shutter?
formal|Open it a little. Don't let the rain blow onto the books.
neutral|Venerable, we counted the donations twice. The numbers match.
formal|Write them in the book before you leave. Memory is not the record.
neutral|Venerable, a visitor is asking for a blessing in another language.
formal|Bring them after the chant. I will speak simply and slowly.
neutral|Venerable, the dogs are at the gate. May I give them the leftover rice?
formal|Not from the offering plate. Use the kitchen scraps, away from the hall.
neutral|Venerable, I don't understand the precept you repeated. May I ask after?
formal|Ask after. Don't stop the group for one question.
neutral|Venerable, the rain came through the window onto the spare robes.
formal|Move them now. Spread them in the room with the fan.
neutral|Venerable, may I light the lamps, or is it too early?
formal|Wait until the yard is dim. Don't waste the oil.
neutral|Venerable, my grandmother can't climb the step. May she sit below?
formal|Yes. Bring her a mat and a cup of water. Don't make her stand.
neutral|Venerable, I will come every Sunday this month if my shift allows.
formal|Come when you can. Don't make a vow you will break in anger at yourself.
neutral|Venerable, the children picked flowers. Are those allowed on the tray?
formal|If they were picked in our yard, yes. Don't send them back for more.
neutral|Venerable, someone left their phone on the mat. I turned the sound off.
formal|Put it on the shelf. Don't look through it.
neutral|Venerable, the meal is ready. Should we call people in from the yard?
formal|Call them once, gently. Those who are speaking can come after.
neutral|Venerable, I feel ashamed about a lie I told at home.
formal|You can tell the truth there first. I will listen if you still need to.
neutral|Venerable, the drum skin is loose in this heat.
formal|Don't tighten it yourself. Tell the one who keeps the instruments.
neutral|Venerable, may I take a photo of the yard and not of people's faces?
formal|Ask each person. The buildings are not the problem. People are.
neutral|Venerable, we are short one bowl. I can run to the kitchen.
formal|Go. Don't run through the seated rows.
neutral|Venerable, the visitor offered money and asked for a promise.
formal|Take no promise you can't keep. The office can record a donation.
neutral|Venerable, I'll wash the cloths after the meal. Where do they dry?
formal|On the back line, in the sun, and bring them in before the evening rain.
neutral|Venerable, my voice shook when I read. I'm sorry.
formal|A shaking voice can still be sincere. Sit down and drink water.
neutral|Venerable, the gate was open when I arrived. I closed it.
formal|Good. Leave it so people can enter, and close it when the yard is empty.
neutral|Venerable, may I sit near the door in case my child needs me?
formal|Yes. Don't pace. Sit, and go out only if he calls.
neutral|Venerable, I brought nothing today except myself. Is that all right?
formal|Yes. Don't apologize for empty hands.
neutral|Venerable, the loudspeaker from the wedding is facing us.
formal|We will wait it out. Don't send anyone to argue in the lane.
neutral|Venerable, I'll walk my mother home before the road is dark.
formal|Go while you can see the lane. Come again when you can.
neutral|Venerable, thank you for speaking slowly. I could follow today.
formal|Then practice one line at home, not the whole chant.
worried|Venerable, there is a man shouting at the gate. He isn't from here.
formal|Don't surround him. One of you come get me, and the rest stay seated.
neutral|Venerable, the floor is still damp where the rain blew in.
formal|Leave that square empty. Nobody sits on wet wood.
neutral|Venerable, I can stay to lock up if you tell me which doors.
formal|The side door and the store room. The main door stays as I left it.
neutral|Venerable, a child put a toy on the offering tray. I removed it.
formal|Give it back to the parent without a speech.
neutral|Venerable, we'll return next week with my sister, if she agrees.
formal|Let her agree herself. Don't volunteer her name today.
neutral|Venerable, the kettle is boiling in the kitchen. Should I pour?
formal|Pour into the large pot, not the small cups yet.
neutral|Venerable, I was angry on the way here. I don't want to bring that inside.
formal|Leave it at the step with your shoes. You can pick the feeling up later if you must.
neutral|Venerable, the list of names is smudged. May I rewrite it?
formal|Rewrite it beside the old one. Don't throw the old list away.
neutral|Venerable, people are asking where to put their shoes. I'll stand and show them.
formal|Show them once. Then let the row of shoes teach the rest.
neutral|Venerable, I have to catch the last bus. May I bow from the door?
formal|Yes. Go. Don't cross the whole hall to make a bigger goodbye.
neutral|Venerable, the fruit is cut and covered. The flies were early.
formal|Keep the cover on until we start. You did the right thing.
neutral|Venerable, I'll come back when I can stay longer than this.
formal|A short visit done carefully is not a small thing.
""".strip().splitlines()

PHONE = """
worried|I can hear the street, not you. Step inside and say it again.
worried|You cut out after the word hospital. Is someone hurt?
neutral|Don't hang up. I'm writing the address down.
neutral|I'm whispering because the baby just fell asleep.
worried|Say the house number once more. I heard fifteen and fifty.
neutral|I'm on the bus. If I lose you, I'll call from the stop.
worried|Mother, the clinic wants you here before noon. Can you leave now?
neutral|I reached the station. The next bus is in forty minutes.
worried|Dad, I missed the turn. I'm at the market with the blue roof.
neutral|Don't shout. I can hear you. The line is clear now.
worried|The nurse said to bring the old prescription. It's in the tin.
neutral|I'll be home after the last bell. Don't wait in the lane.
worried|Stay on the line while I ask someone the street name.
neutral|I bought the rice. Do you still need the oil, or did you get it?
worried|Your voice is shaking. Start again from the beginning.
neutral|I'm with Grandma. She wants to know if you'll come Sunday.
worried|The power is out here. If the phone dies, I'm fine. Don't panic.
neutral|Call me when you see the bridge. I'll come down to the gate.
worried|They moved the meeting earlier. Can you tell the others?
neutral|I can't talk at the counter. I'll call you on my break.
worried|Repeat the medicine name. I don't want to buy the wrong box.
neutral|The rain is loud on this roof. Text me the time instead.
worried|I'm outside the school and I don't see you. Wave if you can.
neutral|Father, the form needs your signature. I'll bring it tonight.
worried|Don't ride in this rain. I'll wait where it's covered.
neutral|I left the key with the neighbor. Knock on the left door.
worried|The baby is hot. I'm taking him in. Meet me if you can.
neutral|We saved you food. It's on the shelf, covered, not in the fridge.
worried|I only have one bar of signal. Say the lane name and stop.
neutral|I'll pay the bill online if you read me the number slowly.
worried|Are you safe? You didn't answer and the news said the road flooded.
neutral|I'm safe. The road is wet and I'm waiting it out at the shop.
worried|Mom, I need you to pick me up. My stomach is bad again.
neutral|Dad, practice ended early. I'm at the usual gate.
worried|The driver doesn't know the alley. I'll get out on the main road.
neutral|Tell Grandma I'll call her after dinner, not during her rest.
worried|I lost my bag on the minibus. The ticket is still in my pocket.
neutral|I'm staying at Sokha's tonight. Don't bolt the gate for me.
worried|The teacher called. It isn't serious. He talked in class. That's all.
neutral|I'll bring the charger. Yours is the white one, yes?
worried|Speak up. A truck is passing and I lost the last sentence.
neutral|The shop still has the eggs. Do you want a dozen or half?
worried|I'm at the wrong clinic. This one doesn't have your name.
neutral|Turn left after the pagoda and I'll be by the drink stall.
worried|Don't let them start without me. I'm ten minutes away.
neutral|I can hear the television behind you. Step into the kitchen.
worried|The fever is the same, not worse. We'll see the doctor in the morning.
neutral|I locked the shop. The shutter is down. You can stop worrying.
worried|Which ward? You said it once and the line dropped.
neutral|I'm on the ferry. I'll call when my feet are on the dock.
worried|Mom, don't cry. I'm all right. The bike fell and I stood up.
neutral|I'll cook if you buy the fish. Call me when you're leaving the market.
worried|The exam starts early. Wake me at five, even if I argue.
neutral|Your brother asked me to tell you he took the blue shirt.
worried|I can't find the house. Flash the porch light if you hear me.
neutral|The package arrived. I'll open it when you get here, not before.
worried|Dad, the landlord is downstairs. He wants the month's number from you.
neutral|I'm whispering in the library. Nod if you can hear me and I'll talk later.
worried|The child is with me. We missed you at the gate. We're by the drinks.
neutral|I'll take the night bus. Don't wait up past ten.
worried|Say the doctor's name again. I want to ask for the right person.
neutral|We're eating at the stall. I'll bring you the sour soup if they have it.
worried|The alarm at the shop went off and stopped. I'm going to look. Stay on the phone.
neutral|It was the neighbor's cat. Nothing is broken. I'm locking up again.
worried|I need the insurance paper. Which drawer, the left or the brown one?
neutral|Left drawer, under the red notebook. Don't bring the whole stack.
worried|My battery is red. If I vanish, I'm on the bus and I'm fine.
neutral|Text me a pin. Hearing the directions isn't working.
worried|Grandma fell but she's talking. I'm with her. Come when you can.
neutral|She wants her own pillow from home. I'll wait with her.
worried|Don't take the flooded lane. Go past the school even if it's longer.
neutral|I already turned around. I'm on the high road now.
worried|The results aren't today. They said tomorrow after two. I'll go.
neutral|I'll meet you in the lobby. Wear the gray shirt so I see you.
worried|I hear you crying. Put the phone down and drink water, then talk.
neutral|I'm calmer. The bill is high and I was ashamed to say the number.
worried|Tell me the number. We'll sort it. Don't handle it alone tonight.
neutral|I'll call the office in the morning. Sleep. I'll set the alarm.
worried|The gate code changed. Nobody told me. Can you open it from inside?
neutral|I'm coming down. Stay where the camera can see you.
worried|I took the wrong bag from the seat. I'm going back to the station now.
neutral|Call me when you have it. I'll tell your sister not to worry yet.
worried|The coughing got worse on the walk. I'm sitting. Don't send anyone yet.
neutral|If it doesn't ease in ten minutes, call me back and I'll come.
worried|I can see the house. Don't come out. The rain is sideways.
neutral|I'll be at the door in one minute. Have the towel ready.
worried|We need to talk about the money, not in a message. Are you alone?
neutral|I'm alone. Say it plainly. I won't interrupt.
worried|The bus broke down past the bridge. We're safe on the shoulder.
neutral|Don't accept a ride from a stranger. Wait for the replacement.
worried|I love you. The line is bad and I wanted that said before it drops.
neutral|I heard you. Call again when you can. I'll keep the phone near me.
worried|Father, the form asks for a witness. Can you come at eight, not nine?
neutral|I'll be there at eight. Bring your own pen. Theirs never works.
worried|I'm lost inside the building. The signs don't match the map you sent.
neutral|Go back to the entrance and wait on the left bench. I'll find you.
worried|The baby grabbed the phone. If you heard nonsense, that was him.
neutral|I heard enough. You're home. That's the part I needed.
worried|Don't hang up until I repeat the address. I get the lane wrong when I rush.
neutral|Blue door, after the clinic, second left. Say it back.
worried|Second left, blue door, after the clinic. I have it. I'm walking now.
neutral|Good. I'll stay outside so you see me. White shirt, black umbrella.
""".strip().splitlines()

MIXED = """
neutral|The lunch order is not your job to guess. Read the slip out loud.
teasing|You saved me the burnt piece again and called it generous.
neutral|I'll take the window seat if you actually want the aisle.
formal|Officer, we live in the blue house. The noise was the gate, not a fight.
neutral|I don't know the man who asked for our alley. I didn't point.
teasing|You studied the wrong page and still walked in like a hero.
formal|Officer, nobody is hurt. The motorbike fell. The rider stood up.
neutral|Excuse me, is this the line for the clinic or for the paperwork?
teasing|You said you hated the song and then hummed it all the way home.
formal|Officer, I can show you the house number. It's on the gate post.
neutral|I'm sorry, I stepped into your photo. I'll move.
teasing|You bring one pen to an exam and then look at me like I planned it.
formal|Officer, the child is mine. We were separated by the crowd for a minute.
neutral|Do you know which bus stops at the hospital gate?
teasing|You promised a short story and talked through the whole ride.
formal|Officer, I don't want to file anything. I want help finding the lane.
neutral|Sorry, is this seat free or are you saving it?
teasing|You wear confidence better than you wear matching shoes.
formal|Officer, the bag is mine. The ticket is in the side pocket.
neutral|I think you dropped this scarf. It was on the bench behind you.
teasing|You got us lost and then blamed the sun for moving.
formal|Officer, we saw the empty house door open. We didn't go in.
neutral|Can you tell me if this alley reaches the river or stops at a wall?
teasing|You said five more minutes three times. I counted.
formal|Officer, my mother is on the phone and frightened. May I explain slowly?
neutral|I'm not from this street. I'm looking for the school with the yellow wall.
teasing|You hide the snacks and forget I watched you hide them.
formal|Officer, the dog is loud but he is tied. He won't reach the lane.
neutral|Excuse me, the sign is torn. Does the bus still stop here?
teasing|You danced one step and spent the night denying it.
formal|Officer, I can wait. Please finish with the person ahead of me.
neutral|Sorry, your book fell when the boat moved. I picked it up.
teasing|You call it a shortcut and we add twenty minutes every time.
formal|Officer, the address on the paper doesn't match the gate. Can you look?
neutral|I don't need a taxi. I'm walking. Thank you anyway.
teasing|You borrowed my jacket and returned it smelling like grilled corn.
formal|Officer, nobody threatened us. We are only lost.
neutral|Is the market this way, or did I pass the turn at the clinic?
teasing|You said you weren't cold and then stole the middle of the blanket.
formal|Officer, I'll move the motorbike. I didn't see the painted line.
neutral|Sorry I brushed your arm. The aisle got tight at the stop.
teasing|You narrate your own card game like a stadium.
formal|Officer, the shouting stopped. It was a wedding speaker, not a fight.
neutral|Do you know a pharmacy that is still open after this hour?
teasing|You hate surprise parties and then sulk when we don't plan one.
formal|Officer, I have the owner's number. May I call before anyone moves the bike?
neutral|I'm looking for the ward entrance, not the main lobby. Did I miss it?
teasing|You pack for a weekend like you're moving house.
formal|Officer, the child found a wallet. We didn't open it.
neutral|Excuse me, would you watch my bag while I buy a ticket at the window?
teasing|You give advice you would never follow, and you know it.
formal|Officer, we can describe the car. We didn't see a plate clearly.
neutral|Sorry, I thought you were my cousin from the back. Wrong person.
teasing|You say you're leaving and then stand in the doorway for another story.
formal|Officer, I'll come to the desk. Please don't shout across the yard.
neutral|Is this the queue for the same window, or did two lines become one?
teasing|You burned the rice and presented it like a new recipe.
formal|Officer, my identification is at home. I can have someone bring it.
neutral|I don't want a tour. I want the road back to the ferry.
teasing|You remember every score and forget where you put your keys.
formal|Officer, the noise complaint is fair. I'll turn the speaker around.
neutral|Excuse me, did the last bus already leave, or is that it at the curb?
teasing|You pretend not to like the sour soup and then finish the bowl.
formal|Officer, nobody is missing. My sister is late, not lost.
neutral|Can you point to the paid exit? I don't want to walk through the wrong gate.
teasing|You took the photo of the food and forgot to eat it.
formal|Officer, I'll answer what I saw. I won't guess the rest.
neutral|Sorry, the umbrella dripped on your bag. Let me wipe it.
teasing|You call me dramatic and then gasp at the weather report.
formal|Officer, the gate sticks. We aren't forcing it. It's our house.
neutral|I'm trying to reach the night market. Is it past the bridge or before?
teasing|You said the movie was too long and quoted it all evening.
formal|Officer, thank you. We know the way from here.
neutral|Excuse me, is the clinic upstairs or is upstairs only offices?
teasing|You lend things with a speech and take them back with another speech.
formal|Officer, the crowd pushed us. We didn't mean to block the door.
neutral|I think this is your stop too. The sign says hospital, not market.
teasing|You get quiet when you're happy and loud when you're fine. It's confusing.
formal|Officer, I'll wait on the side. Tell me when it's my turn to speak.
neutral|Sorry to interrupt. Does this road flood, or only the lane behind it?
teasing|You planned a surprise that everyone already knew about.
formal|Officer, the bag is light because it's clothes, not anything else.
neutral|I'm new on this bus route. Please tell me when we reach the river road.
teasing|You complain about the heat and stand in the sun to make the point.
formal|Officer, we will move the chairs in from the lane before dark.
neutral|Excuse me, the child is trying to ask you which boat is theirs.
teasing|You say one dish and then eat from every plate as research.
formal|Officer, I understand. We'll take the long way around the barrier.
neutral|Thank you for the directions. If I get it wrong, the blue roof is the landmark.
teasing|You were going to be early and arrived with the story of why not.
formal|Officer, that's all we saw. We don't want to add to it.
neutral|I'm sorry I don't speak more clearly. Is the school straight ahead?
teasing|You protect the last piece and then give it away when someone looks sad.
formal|Officer, my phone is dead. May I write the report number down?
neutral|The line moved. You're next, not me. I was only holding your place.
teasing|You call the detour a scenic route after we're already late.
formal|Officer, we'll come back with the paper in the morning. Nothing is urgent tonight.
neutral|Excuse me, I think you left your change on the counter. Here.
teasing|You hate being teased and then start it every time.
formal|Officer, thank you for not rushing us. The address is right now.
neutral|I'll walk with you as far as the light. After that, our roads split.
""".strip().splitlines()

EXTRAS = {
    "child_to_parent": """
worried|Mom, the mat is wet where the window doesn't latch.
neutral|Dad, can I trade chores with my sister just for today?
happy|Mom, the hen has chicks under the house. Come see, quietly.
worried|Dad, I bit my tongue and it won't stop tingling.
neutral|Mom, I put the soap back. It was on the rim of the bucket.
tired|Dad, can we skip the market? My feet are blistered.
neutral|Mom, the clock stopped. I don't know if I'm late.
worried|Dad, a dog followed me and wouldn't turn at the corner.
happy|Mom, I helped Grandma shell the beans without being asked.
neutral|Dad, may I use the radio quietly while I sweep?
sad|Mom, they laughed at my shoes. I don't want to go tomorrow.
worried|Dad, the oil lamp smoked up the wall. I blew it out.
neutral|Mom, I saved the stems the way you showed me.
neutral|Dad, can you sign this before you leave for work?
happy|Mom, I found the earring under the bed. It was standing up.
worried|Dad, my ear hurts when the wind hits it on the bike.
neutral|Mom, I watered the pots. The big one drank the whole cup.
tired|Dad, please don't send me back out. The rain just got harder.
neutral|Mom, the rice crust is burnt on one side only.
worried|Dad, I think a nail went into my slipper. Don't let the baby walk there.
happy|Mom, the teacher read my sentence to the class.
neutral|Dad, can I have the heel of the bread for the walk?
sad|Mom, I miss Grandpa today. Can we look at the photo?
worried|Dad, the cage door is open and I don't see the bird.
neutral|Mom, I folded the shirts wrong. Will you show me again?
neutral|Dad, I'll carry the empty jugs if you carry the full one.
happy|Mom, the custard man gave me an extra spoonful.
worried|Dad, my knee is scraped and the dust is in it.
neutral|Mom, can we call Auntie tonight? She said she would wait.
tired|Dad, I nodded off on the homework. Wake me in a little while.
neutral|Mom, I left your scissors on the high shelf so the baby can't reach.
worried|Dad, the neighbor said our ball hit their shutter. I'm sorry.
happy|Mom, I can read the sign on the clinic by myself now.
neutral|Dad, may I sit in the front of the bike if I hold on?
neutral|Mom, the soup needs water. It went thick while I was outside.
worried|Dad, I heard a drip in the wall. It wasn't the roof.
neutral|Mom, I told the truth about the broken cup.
sad|Dad, nobody picked me for the team. Can I practice with you?
neutral|Mom, I'll sleep early. Please don't let me miss the morning bell.
worried|Dad, the charcoal bag tore and the pieces are on the step.
happy|Mom, Grandma said I can stay for the whole Sunday.
neutral|Dad, can you reach the ball on the roof without the bad ladder?
neutral|Mom, I washed the fruit. The mango was already soft.
worried|Dad, my chest feels tight after running. It goes away if I sit.
neutral|Mom, I put the money in the tin, not in my pocket.
tired|Dad, the sun gave me a headache. Can I lie in the dark room?
neutral|Mom, the baby likes the song you hummed. Do it again.
worried|Dad, I locked the gate and the key is still in it outside.
happy|Mom, I didn't cry at the clinic this time.
neutral|Dad, may I walk with Piseth if his mother says yes?
""".strip().splitlines(),
    "parent_to_child": """
neutral|Cap the pen. It leaked in the bag last time.
worried|If your head still pounds after water, we don't go to practice.
neutral|Put the wet cloth on the line, not on the chair.
tender|You waited your turn. I saw it. That was hard and you did it.
neutral|Don't peel the sticker off the fruit. We need to know the price.
worried|The road is slick. Walk the bike until the corner.
neutral|Leave a light on for your sister. Her key sticks.
tender|I like hearing you read even when you stumble.
neutral|Shake the sand off your feet before the mat.
worried|Don't taste the sauce from the spoon that stirred the raw meat.
neutral|Your shirt is on the nail. I mended the pocket.
neutral|Tell me the truth if you spent the coin. I won't shout.
worried|The jar lid is glass. Carry it with two hands.
neutral|We'll leave when the rice is packed, not before.
tender|You noticed Grandma was cold and brought the scarf. Good.
neutral|Don't interrupt your father mid-sentence. Wait for the pause.
worried|If the dog growls, you stop. You don't prove you're brave.
neutral|The homework stays on the table so it doesn't vanish into the bed.
neutral|Eat the cucumber. You asked for it and then made a face.
worried|Don't touch the grinder while it is plugged in.
neutral|I'll braid it loosely so it doesn't pull. Hold still.
tender|You shared without being watched. That's the kind I trust.
neutral|Bring the cups in before the wind knocks them off the rail.
worried|The fever cloth goes on the forehead, not the eyes.
neutral|Say good night to your brother even if you're annoyed.
neutral|The market bag has a hole. Use the other one.
worried|Don't run with a stick. I don't care that everyone else does.
neutral|We'll call your aunt after dinner. Remind me so I don't forget.
tender|I'm glad you came to tell me yourself.
neutral|Put the battery torch back on the hook when you come in.
worried|If you vomit again, we are done with the festival tonight.
neutral|The shoes by the door are a pair. Don't take one of each.
neutral|Speak to the teacher with the same tone you use with me.
worried|Don't climb for the kite. We'll buy string, not a broken arm.
neutral|Your water bottle is in the side pocket. I filled it.
tender|You were patient with the baby. I know he pulled your hair.
neutral|Close the rice so it doesn't dry out by morning.
worried|The cut gets washed before the plaster. Don't skip the wash.
neutral|We'll walk, not ride, until the chain is fixed.
neutral|Leave the good scissors in the drawer. Use the school pair.
worried|If a stranger offers a ride, you say no and come home.
neutral|The sour soup is salty enough. Don't add fish sauce on top.
tender|I kept the drawing. It's on the cupboard where I see it.
neutral|Napkin on the lap if we have guests. At least try.
worried|Don't swing the door. The hinge pin is rising.
neutral|Your brother gets the front today. You had it yesterday.
neutral|I'll check the sums after I wash my hands. Leave them open.
worried|The well is not a dare. You don't lean over it.
neutral|Pack the raincoat even if the sky looks bored.
tender|You apologized without me writing the script. I'm proud of that.
neutral|Lights out after the story, not after a second story.
""".strip().splitlines(),
    "romantic": """
tender|I kept the seat dry with my bag. Sit before the rain finds it.
neutral|If your mother wants me to leave early, I will. Tell me straight.
happy|You laughed at the wrong moment in the story and I liked it more.
worried|Don't cross against that light to save two minutes with me.
neutral|I'll wait outside the shop. Take the time you need with your brother.
tender|Your hand is cold. Put it in my pocket until the bus comes.
neutral|We can cancel tonight. A quiet no is better than a tired yes.
happy|I saw you before you saw me. You were counting change so carefully.
worried|If he follows us again, we go into the shop with the lights on.
neutral|I'll learn the dish your father likes. Tell me what not to add.
tender|Stay until the song ends. The road will still be there.
neutral|Don't buy me anything. Walk with me. That's the evening.
happy|You remembered the spicy one is yours and the plain one is mine.
worried|The message can wait. I want your voice, not another line of text.
neutral|I'll stand on the step so your neighbors don't have to wonder.
tender|You fell asleep on my shoulder for one stop. I didn't move.
neutral|Tell me if this is too many nights in one week.
happy|The photo is crooked and your eyes are closed. I'm keeping it.
worried|Don't joke that you'll disappear. I don't find that funny.
neutral|I'll bring the umbrella big enough for both, not the pocket one.
tender|Come in from the doorway. You're letting the mosquitoes draft behind you.
neutral|We can talk about the money without turning it into a test.
happy|You waved like you weren't sure I'd see you. I did.
worried|If you're ashamed of me in front of them, say that here first.
neutral|I'll leave at nine even if the story isn't finished. You have work.
tender|The tea is too strong. I'll add water. Don't drink it to be polite.
neutral|Walk on the shop side. The bikes clip the curb on the other side.
happy|You wore the shirt I said looked like rain. It does, in a good way.
worried|Don't read his old messages to prove something. I believe you.
neutral|I'll meet your sister when you want, not because the calendar says so.
tender|Put your head down. I'll watch the stop and wake you.
neutral|We don't have to name this tonight. We can just get home dry.
happy|You saved the lime wedge. You always do that and I always notice.
worried|The road is flooded at the usual corner. Take the school way. I'll wait.
neutral|I'll pay this time. You paid the ferry. Don't argue in the rain.
tender|Your ear is cold. That's the only reason I'm this close. Mostly.
neutral|If you need a night with your family, take it. I'll call tomorrow.
happy|The song came on at the stall and you didn't change it. Thank you.
worried|Don't let me be the reason you miss the last bus. Go.
neutral|I'll stand where you can see me when you come out of the clinic.
tender|You don't have to talk. The walk is already enough.
neutral|I'll learn to be quieter in your lane. Tell me when I miss it.
happy|You looked back twice. I was still there the second time.
worried|If your answer is no, say no. I can hear a real no.
neutral|I'll bring the sour soup, not flowers. You said flowers die in this heat.
tender|Stay for the rain. It will be louder than anything we need to decide.
neutral|Text me one word when you're inside. I'll sleep after that.
happy|You got the order right and looked proud. It was a small thing and it wasn't.
worried|Don't share my photo in the group. I didn't agree to that.
neutral|I'll wait under the pharmacy sign. If I'm late, it's the bus, not doubt.
tender|Give me your bag. Your shoulder has been up by your ear all evening.
neutral|We can be ordinary. I think that's what I came here to ask.
""".strip().splitlines(),
    "friends_close": """
neutral|I'll take notes if you actually show up before the teacher does.
happy|They had the sour drink you like. I bought two. Yours is sweating on the bench.
worried|Don't joke with that group. They weren't laughing with you.
neutral|You can copy the diagram, not the paragraph. Write your own sentence.
teasing|You stretched one snack into a whole personality.
neutral|I'll save the seat on the aisle. You get sick at the window.
worried|Your lip is split. Who did that? Don't shrug it off.
happy|The coach said your pass was the reason the play worked.
neutral|Meet me by the racks. The gate crowd makes me miss you every time.
teasing|You revised the plan until the plan was to stand still.
neutral|I'll return the jersey washed. Don't let your brother wear it first.
worried|The shortcut floods. I don't care that it saves four minutes.
happy|You remembered my sister's name. She'll pretend not to care.
neutral|Lend me the charger until the bell. I'll hand it back in the doorway.
teasing|You brought a speech to a conversation.
neutral|I'll walk you home if we leave before the shop lights go off.
worried|Don't get in if the driver won't name the fare first.
happy|The photo is terrible and accurate. I'm sending it.
neutral|You talk. I'll watch the bags. Then we switch.
teasing|You said you were fine in the voice you use when you're not.
neutral|I'll ask the teacher if you stand next to me and don't vanish.
worried|Your hands are shaking. Sit on the step and drink this.
happy|We found the cheap tickets and they were real. I'm shocked too.
neutral|Hold my place. If they call my name, say I'm in the washroom.
teasing|You packed three shirts for a day and forgot the assignment.
neutral|I'll be at the juice stall. Don't make me come find you in the games row.
worried|Don't swim off the rocks. The sign is new because someone didn't.
happy|You got the pronunciation and didn't even look proud. I am.
neutral|Wake me at the hospital stop, not the market. I mix them up when I'm asleep.
teasing|You narrated the entire bus ride to a stranger who wanted a nap.
neutral|I'll share the notes if you share the summary. Both, not one.
worried|The dog on that step isn't tied. Cross now.
happy|They clapped for you and you looked at me like it was a mistake. It wasn't.
neutral|You can have the last bite. I watched you pretend not to want it.
teasing|You studied the map and still followed me into the wrong lane.
neutral|I'll tell your mother you were with me if that's the truth. Only if it is.
worried|Don't laugh near the funeral house. Walk quiet until the next corner.
happy|The vendor knew your order. You're a regular. Congratulations.
neutral|Count the change before we leave the window. I'm tired of their shortages.
teasing|You said "one game" and the sun moved.
neutral|I'll carry the speaker. You apologize to the neighbor in advance.
worried|Your shoe is untied and the step is metal. Fix it.
happy|You passed the oral. I heard you from the hall and I didn't breathe.
neutral|Leave when I leave. I don't want to walk that lane alone tonight.
teasing|You gave away the plan and then whispered the rest.
neutral|I'll quiz you on the way. Wrong answers cost you a sip of the warm soda.
worried|Don't pick that up. You don't know why it was left on the wall.
happy|The rain waited until we were under the awning. Take the credit anyway.
neutral|You owe me a pen. I'm writing it here so future you can't negotiate.
teasing|You got sunburned on one arm and called it a design.
neutral|I'll see you at the racks. If I'm not there, I got kept behind. Don't wait past dark.
worried|Text your brother. You said you would and then you started another story.
""".strip().splitlines(),
    "siblings": """
neutral|I'll take the early well run if you start the rice.
worried|Don't tell them I cried. I'll tell them myself if I have to.
teasing|You rehearsed the apology to the mirror and it still came out sideways.
neutral|The uniform shirt is the one with the button I sewed, not the torn one.
worried|The baby has a coin in his fist. Get it before it goes in his mouth.
neutral|I'll quiz you if you stop reading the answers out loud first.
teasing|You hid the comic in the grammar book. The book isn't that thick.
neutral|Wake me if Mom's key hits the gate. I want to look awake.
worried|The oil is popping. Turn it down before it hits your arm.
neutral|Your ribbon is on my wrist. I found it in the wash and forgot.
teasing|You claim the fan and then fall asleep facing the other way.
neutral|I'll walk you if you carry the bottles. My hands are full of books.
worried|Don't open Dad's letter. The seal is still flat and it isn't ours.
neutral|The mosquito coil goes on the dish, not on the wood.
teasing|You sang the wrong words with full confidence.
neutral|I'll save you the crispy bit if you don't announce it to the room.
worried|The step is slick. Hold the rail and don't race me tonight.
neutral|Your pencil case is in my bag. I grabbed it by mistake.
teasing|You studied my notes and still wrote your own wrong date.
neutral|I'll sleep closest to the door. You hate the hallway noise.
worried|Don't let the baby see the knife on the low stool.
neutral|The good scissors stay in the drawer. I need them for the costume hem.
teasing|You told the story like you weren't the one who fell.
neutral|I'll call Grandma if you chop the onions. My eyes quit first.
worried|The neighbor knocked twice. If it's the third time, we answer together.
neutral|Your left shoe is under my mat. I kicked it there in the dark.
teasing|You said you'd be quiet and then narrated making tea.
neutral|I'll iron the collar. You do the buttons. Don't swap and vanish.
worried|The gas smelled for a second. I checked. The knob is off. Still tell Dad.
neutral|Don't use my exam pencil. It smears and I'll get blamed for the dots.
teasing|You borrowed my calm and returned it as a speech.
neutral|I'll take the floor pallet. Your back was worse yesterday.
worried|The dog is whining at the wrong hour. Come look before we wake them.
neutral|The charger stays in the hall. You disappear with it.
teasing|You lost the game and explained the rules to the winner.
neutral|I'll pack both lunches. You write the names so we don't swap the spicy one.
worried|Don't climb past the third branch. The one above it broke under me last year.
neutral|Your hair tie is on the sink. I washed it. It's still wet.
teasing|You practiced looking casual and looked like a person waiting for a bus.
neutral|I'll read the little one the short book. You get the dishes. Fair.
worried|Mom's voice went flat on the phone. Stay nearby when she comes in.
neutral|The raincoat with the torn sleeve is mine. Yours is the blue one.
teasing|You hid behind me and then said you weren't shy.
neutral|I'll set the alarm on my phone. Yours sleeps through anything.
worried|The ceiling stain grew. Don't put the bed back under it.
neutral|Your library card is in the cup by the salt. Don't ask me tomorrow.
teasing|You apologized to the dog more sincerely than to me.
neutral|I'll close the shutters. You get the cups off the rail.
worried|Don't joke about leaving home. They don't hear it as a joke.
neutral|The story can wait. Blow out the lamp. We're both useless tomorrow if we don't.
""".strip().splitlines(),
    "elder_home": """
neutral|Bring the low stool. My knees don't like the step today.
worried|Don't run water over that cut. Pat it. I'll look in the light.
tender|You came in quietly so I could finish the nap. I heard you anyway.
neutral|The good cups are for guests. We can chip the ordinary ones.
worried|The lane dog is new. Don't put your hand out just because he wags.
tender|Tell me one true thing from school, not the tidy version.
neutral|The fan goes off when you leave the room. The bill arrives either way.
worried|If the dizziness comes back, you sit on the floor, not the step.
""".strip().splitlines(),
    "neighbors": """
neutral|I'll roll your bin in if the wind starts. Mine already walked once.
worried|The shared tap is running when nobody is there. I'll shut it and tell you.
neutral|Your visitor left a umbrella. It's hooked on my shutter.
happy|The kids returned the chalk. They even swept the marks. Mostly.
worried|A scooter is idling with the lights off. I'm not opening the gate.
""".strip().splitlines(),
    "travel": """
neutral|Keep the paper ticket even after they tear the stub. The stub isn't the whole proof.
worried|The van roof rack is loose. Don't let them put the soft bag on top.
neutral|If we get separated, we meet at the ticket window, not at the food row.
happy|The sea is on the left now. You can stop checking the map every minute.
worried|Don't step on the wet paint at the dock edge. The board is marked and people miss it.
neutral|I'll ask for two seats on the shaded side. You watch the child and the bags.
worried|The driver turned the music up and the speed with it. Say the destination again, calmly.
neutral|We get off one stop early if the road is flooded. I'd rather walk the bridge than sit in it.
happy|The conductor repeated our stop without being asked. Good sign.
worried|Don't follow the person offering a cheaper boat. We paid at the window.
neutral|Hold the address card up. Pointing and hoping is how we missed the lane last time.
worried|The footboard is slick. Both hands on the rail until you're actually on the boat.
neutral|I'll send the plate number before the door closes. If I don't, don't let the car leave.
worried|The sky went green over the far bank. If they wave us back, we go back.
neutral|Count heads and bags when we stand up. We do it every time and one day it will matter.
""".strip().splitlines(),
}

GROUPS_C = (
    ("school", "teacher_to_student", "formal", "classroom", SCHOOL),
    ("clinic", "patient_to_doctor", "formal", "clinic", CLINIC),
    ("pagoda", "lay_to_monk", "formal", "pagoda", PAGODA),
    ("phone_call", "phone_call", "casual", "phone", PHONE),
    ("mixed_day", "coworkers", "casual", "street", MIXED),
)
