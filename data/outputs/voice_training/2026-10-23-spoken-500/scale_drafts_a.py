"""Original synthetic lines, groups 1–5. Not commercial dialogue."""
from __future__ import annotations

# category, relationship, register, setting, people, emotion|text lines
CHILD = """
worried|Mom, the charcoal stove is still smoking after breakfast.
worried|Dad, my stomach feels tight after that sour soup.
neutral|Mom, can I take the leftover rice to the school gate tomorrow?
worried|Dad, the teacher said I kicked the ball into the window.
neutral|Mom, I can't find my other sandal under the bench.
happy|Dad, the puppy followed me from the lane and sat down.
worried|Mom, the power is out and I can't finish the reading.
neutral|Dad, may I sleep at Grandma's house on Friday night?
sad|Mom, I spilled soy sauce down my white shirt again.
tired|Dad, the neighbor's radio was on before sunrise.
neutral|Mom, this collar itches. Can I change shirts?
afraid|Dad, I saw a long snake by the well just now.
neutral|Mom, can you tie my hair before we walk out?
neutral|Dad, the water jug is empty and I'm still thirsty.
worried|Mom, the baby is crying in the hammock and won't settle.
neutral|Dad, may I borrow the small flashlight for the yard?
happy|Mom, I got every sum right on the practice sheet.
worried|Dad, the bicycle chain came off halfway down the lane.
neutral|Mom, can we buy eggs on the way home from school?
tired|Dad, I walked the long way because the short path is mud.
neutral|Mom, I put the shoes in a row by the door.
worried|Dad, the roof is dripping onto my mat again.
happy|Mom, Auntie said I may help sell drinks on Sunday.
neutral|Dad, can I feed the chickens before it gets dark?
sad|Mom, the other children left me out of the game.
worried|Dad, I think I left my notebook on the classroom bench.
neutral|Mom, the rice is warm. Should I set out two bowls?
afraid|Dad, someone is knocking and I don't know the voice.
neutral|Mom, can I wear the blue shirt to the market?
tired|Dad, my legs hurt from carrying the water twice.
happy|Mom, look, the bean sprouts finally came up.
worried|Dad, the gas smells near the stove. Don't light it yet.
neutral|Mom, I washed the spoons and left them in the rack.
neutral|Dad, may I sit on the step until the rain slows?
sad|Mom, I tore the page and I can't tape it straight.
worried|Dad, the dog won't come out from under the house.
neutral|Mom, can you check if my fever is still there?
happy|Dad, I saved you the sweet piece of mango.
neutral|Mom, I swept the front room and shook the mat.
tired|Dad, can I lie down before we go to the shop?
worried|Mom, the ants are in the sugar jar again.
neutral|Dad, I hung the wet shirts on the back line.
afraid|Mom, the thunder is close. Can I stay in here?
neutral|Dad, may I take one banana for the walk?
happy|Mom, Grandma said my reading is getting clearer.
worried|Dad, the bucket handle cracked when I filled it.
neutral|Mom, I closed the shutters on the windy side.
sad|Dad, I lost the coin you gave me for bread.
neutral|Mom, can we eat early? I'm hungry from the game.
worried|Dad, the baby pulled the cloth and the cup tipped.
""".strip().splitlines()

PARENT = """
worried|Wash your hands before you touch the rice pot.
neutral|Finish the greens first. Then you can have fruit.
tender|Come here and let me see that scrape.
neutral|Put the shoes in a pair so we can find them.
worried|Don't stand on that chair. Call me if you need the shelf.
neutral|Take the umbrella. The lane floods when it pours.
tender|You did the whole page. I'm proud of the neat lines.
neutral|Speak softly. The baby just went down.
worried|If the cough is still there at dawn, we go to the clinic.
neutral|Turn the stove off when the kettle sings.
neutral|Fold the blanket so it dries by evening.
worried|Stay where I can see you at the market.
neutral|Bring the empty bottles back. Don't leave them at school.
tender|Sit with me a minute. Tell me about the game.
neutral|Lock the gate when you come in, even if it's still light.
worried|That fruit is too green. It will hurt your stomach.
neutral|Set the table for four. Uncle may stop by.
neutral|Hang your uniform so it isn't crushed in the morning.
worried|Don't open the door until you hear my voice.
tender|You were brave at the clinic. Rest now.
neutral|Carry the bag on your shoulder, not by the torn handle.
neutral|Sweep the step before guests step in the mud.
worried|The road is dark. Wait and we'll walk together.
neutral|Drink water before you ask for another soda.
neutral|Put the knife back in the drawer when you finish the mango.
tender|I saved your place. Eat while it's warm.
neutral|Tell the teacher I'll come on Thursday after work.
worried|Don't chase the dog into the street.
neutral|Count the change twice and put it in the tin.
neutral|Close the rice pot or the flies will get in.
worried|Your sister is smaller. Let her have the front of the bike.
neutral|Wipe the table before you put the books down.
tender|I heard you help Grandma. That matters to me.
neutral|Take the flashlight if you go to the latrine.
worried|Don't touch the outlet with wet hands.
neutral|Leave a bowl for your father. He'll be late.
neutral|Tie the sack before you carry it. The beans leak.
worried|If you feel dizzy, sit down and call me.
neutral|Brush your teeth. We leave when the bell from the corner rings.
tired|I need ten quiet minutes. Then I'll hear your story.
neutral|Put the wet umbrella in the bucket, not on the mat.
worried|Don't repeat that insult. We don't talk like that here.
neutral|Pack the leftover soup. You can warm it at noon.
tender|You told the truth about the broken cup. Thank you.
neutral|Walk on the inside of the lane, away from the cars.
worried|The fever cloth is warm. Let me change it.
neutral|Ask before you lend my scissors to anyone.
neutral|Stack the chairs so the floor can dry.
worried|Don't climb the mango tree after rain. The bark slips.
neutral|Tell me when the tank is low. I'll call for water.
""".strip().splitlines()

ROMANCE = """
tender|I saved you a seat under the awning, away from the drip.
happy|The noodles are ready. Come eat before they go soft.
neutral|Text me when the bus turns onto the river road.
tender|I like the way you laugh when the story gets silly.
neutral|Can we walk the long way home tonight?
worried|You sounded tired on the phone. Did you eat?
happy|I found the song you hummed. I'll play it low.
neutral|Bring a jacket. The ferry wind is cold after dark.
tender|Hold my bag a second. I want both hands for the cups.
neutral|Let's leave before the market closes the side gate.
worried|I waited by the clinic door. Did I miss you?
happy|You remembered the extra lime. Sit down.
neutral|I'll walk you to the corner, then I have to turn back.
tender|Your hair still smells like rain. Come in.
neutral|Don't buy the tickets yet. I might finish late.
worried|Tell me if your mother doesn't want me there.
happy|The lamp on your step was on. I knew you were home.
neutral|Can we talk after you close the shop, not in the aisle?
tender|I kept the note you wrote. It's in my wallet.
neutral|The rain started. Share the umbrella or we'll both soak.
worried|You went quiet when he joked. Are you all right?
happy|I brought the mangoes you like, the small sweet ones.
neutral|Let's not promise Sunday if your shift can change.
tender|Stay for one more song. Then I'll let you sleep.
neutral|I'll meet you where the lane splits by the tailor.
worried|Don't ride home alone if the streetlight is still out.
happy|You waved from the bus window. I saw you.
neutral|Order for me if the line is long. I'll pay you back.
tender|I saved the last piece because you always give yours away.
neutral|Can we sit somewhere quieter than the river wall?
worried|Your voice shook. Tell me what the message said.
happy|The photo came out. You were looking at the boats.
neutral|I'll carry the bag of rice. You take the greens.
tender|Come closer. I can't hear you over the generator.
neutral|Don't wait in the rain. Step into the shop doorway.
worried|If your brother is angry, I'll speak to him myself.
happy|You wore the blue shirt. I hoped you would.
neutral|Let's leave the party when the speeches start.
tender|I made too much soup. Stay and help me finish it.
neutral|Call when you reach the bridge so I know you're across.
worried|Don't joke about leaving. I need a plain answer.
happy|The flowers are from the stall, not a big shop. Still yours.
neutral|I'll be at the gate at six, even if the bus is late.
tender|Rest your head. I'll wake you before the last ferry.
neutral|We can walk and not talk for a while. That's fine.
worried|You didn't answer at noon. I started to worry.
happy|I kept our cups. We can use them on the roof again.
neutral|Tell me the truth about the job, even if it's a no.
tender|I like ordinary nights with you more than the loud ones.
neutral|Lock the bike to mine so we don't lose the spot.
""".strip().splitlines()

FRIENDS = """
neutral|I'm running late. Start on the homework without me.
happy|Save me a place in the shade. I'm bringing the drinks.
neutral|You left your charger on my desk. I'll bring it tomorrow.
teasing|You said five minutes and the noodles went cold.
neutral|Can you cover my shift until four? I'll take yours Friday.
worried|You look pale. Sit down before we cross the road.
happy|The coach put you on the list. I saw the paper.
neutral|Don't wait at the main gate. The side door is open.
teasing|You always pick the burnt piece and call it lucky.
neutral|I'll walk with you as far as the bridge.
worried|Text me when you're inside. The lane is dark tonight.
happy|We won the practice match. Don't tell the whole class yet.
neutral|Lend me a pen that works. Mine skipped on the test.
teasing|You studied the wrong chapter and still looked confident.
neutral|Meet me by the juice stall, not inside the crowd.
worried|Your bag is open. The wallet is about to fall.
happy|I kept the ticket stub. We should go again.
neutral|Can I copy the diagram after class, not during it?
teasing|You fell asleep in the last row and snored once.
neutral|I'll return the book before the library locks the gate.
worried|Don't get on that bus. The sign says it's full.
happy|Your joke landed. Even the strict one smiled.
neutral|Hold my place in line. I need to buy a bottle of water.
teasing|You brought snacks for yourself and then shared them anyway.
neutral|Let's finish the project at your place. Mine is too loud.
worried|You didn't come to practice. Are you sick or just hiding?
happy|I recorded the song badly, but the chorus is there.
neutral|Walk slower. My sandal strap is slipping.
teasing|You claimed the window seat and then gave it up.
neutral|I'll tell the teacher we split the work down the middle.
worried|Don't swim there. The current sign is new.
happy|The photo of us is funny. Send it to me.
neutral|Can you wake me if I doze off before our stop?
teasing|You memorized the menu and forgot the assignment.
neutral|Leave my helmet on the hook. I'll ride back at dusk.
worried|Your phone is almost dead. Use mine to call home.
happy|We found the cheap seats and they were actually good.
neutral|Count me in for Sunday, unless my mother says no.
teasing|You got lost between two stalls and blamed the map.
neutral|I'll carry the speaker. You take the cable bag.
worried|Don't laugh yet. He might have heard us.
happy|You passed. I watched you refresh the page twice.
neutral|Let's leave before they ask us to help pack the chairs.
teasing|You said you weren't hungry and ate half of mine.
neutral|Meet me after the bell, by the bicycle racks.
worried|Your knee is swelling. Skip the second game.
happy|The vendor gave us an extra skewer. Your luck.
neutral|I'll wait ten minutes. Then I'm going in without you.
teasing|You wore mismatched socks and called it a plan.
""".strip().splitlines()

SIB = """
worried|Sis, the kettle is boiling over. What should I do?
neutral|Move your books. I need the table for one hour.
teasing|You used my shirt and left it in a heap again.
neutral|I'll wash the dishes if you sweep the step.
worried|The baby climbed onto the stool. Come quick.
neutral|Don't tell Mom I ate the last banana. I'll replace it.
teasing|You sing in the shower loud enough for the lane.
neutral|Can I borrow your ruler? Mine snapped in the bag.
worried|Someone is at the gate asking for Dad. Stay with me.
neutral|I saved you rice. It's under the upside-down plate.
teasing|You fell asleep on the homework and drooled on the page.
neutral|Turn the fan toward the middle. I'm melting over here.
worried|The gas knob was left open a little. I closed it.
neutral|Walk me to the corner. I don't want to go alone.
teasing|You take forever in the bathroom when I'm already late.
neutral|I'll help you with the sums after I hang the clothes.
worried|Don't let the dog out. The gate on the lane side is open.
neutral|Your uniform is on the chair. I ironed the collar only.
teasing|You blamed me for the muddy floor and your shoes are worse.
neutral|Can we share the earphones on the bus ride?
worried|Grandma called twice. One of us should call back.
neutral|I left the key under the mat. Don't forget it there.
teasing|You practiced the speech to the mirror for an hour.
neutral|I'll take the early chores if you cook tonight.
worried|The ceiling is dripping on your bed. Shift the mat.
neutral|Don't read my notebook. The ribbon means it's shut.
teasing|You think you hid the snacks. I can see the jar.
neutral|Hold the ladder. I need the box on the high shelf.
worried|Mom sounded upset on the phone. Sit with me when she tells us.
neutral|I'll braid your hair if you stop wiggling.
teasing|You lost the remote and it was in your own pocket.
neutral|Wake me when Dad's bicycle bell rings in the lane.
worried|The neighbor said our music is too loud. Turn it down.
neutral|I packed your lunch. Don't trade the egg away.
teasing|You copied my answer and copied the mistake too.
neutral|Can you watch the pot while I run to the shop?
worried|Don't open that letter. It's addressed to both parents.
neutral|I'll sleep on the floor tonight. You take the mat.
teasing|You said you were studying and the comic was inside the book.
neutral|Tie the mosquito net. The gaps are on your side.
worried|I heard a noise in the kitchen. Come with me.
neutral|Your shoes are by mine. I won't hide them this time.
teasing|You grew taller and still can't reach the good mangoes.
neutral|I'll quiz you on the words if you quiz me on the dates.
worried|Don't ride double on the bike. The tire is already soft.
neutral|Leave the light on in the hall until I'm back from the well.
teasing|You snore when you sleep facing the wall. Just so you know.
neutral|I'll tell them you helped, because you did.
worried|The soup boiled dry at the edge. I added water.
neutral|Share the blanket. The fan is too strong for one person.
""".strip().splitlines()

GROUPS_A = (
    ("child_to_parent", "child_to_parent", "neutral", "home", CHILD),
    ("parent_to_child", "parent_to_child", "neutral", "home", PARENT),
    ("romantic", "romantic", "casual", "evening", ROMANCE),
    ("friends_close", "friends_close", "casual", "street", FRIENDS),
    ("siblings", "older_to_younger_sibling", "casual", "home", SIB),
)
