"""Write kp-2201–kp-2400 source rows into a new train-pool file.

Reads spoken_scale.jsonl and spoken_train_next.jsonl only to reject duplicate
source text. Does not write those files, does not fill candidates, and does
not start a trainer.

The refusal is the same gate as write_train_next.py: exact normalized copies,
content-word overlap at or above 0.42, and shared content 5-grams. This pass
applies that gate to kp-001–kp-2200 and inside the new file.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from collections import Counter
from pathlib import Path

from claynext.models.khmer_spoken.schema import SCHEMA_VERSION

ROOT = Path(__file__).resolve().parents[4]
SCALE = ROOT / "data/khmer_spoken/workspace/spoken_scale.jsonl"
PRIOR = ROOT / "data/khmer_spoken/workspace/spoken_train_next.jsonl"
OUT = ROOT / "data/khmer_spoken/workspace/spoken_train_next2.jsonl"
GATE = ROOT / "data/outputs/voice_training/2026-10-26-spoken-next/write_train_next.py"

LICENSE_NOTES = (
    "Synthetic spoken-dialogue draft for the train pool after kp-2200. "
    "Original English line, checked against kp-001 through kp-2200. "
    "Licence unknown. Not gold. Not human. Pending native review. "
    "Not a weight update."
)
REVIEWER_NOTES = (
    "Synthetic English source only. No reference Khmer. "
    "review_status pending_native_review. Not gold. Not human."
)

EMOTIONS = [
    "neutral", "worried", "neutral", "happy", "tired",
    "worried", "neutral", "teasing", "tender", "neutral",
    "worried", "neutral", "happy", "tired", "neutral",
    "worried", "tender", "neutral", "happy", "worried",
]
HELPERS = [
    "srey", "dara", "lina", "vuthy", "nita",
    "bopha", "rith", "piseth", "sokha", "channary",
]
BLOCKS = [
    ("pottery_kiln", "potter_mao", "potter_to_apprentice", "apprentice_to_potter", "casual"),
    ("silk_loom", "weaver_sreymom", "weaver_to_apprentice", "apprentice_to_weaver", "casual"),
    ("pharmacy_counter", "pharmacist_ly", "pharmacist_to_customer", "customer_to_pharmacist", "formal"),
    ("photo_studio", "photographer_chan", "photographer_to_client", "client_to_photographer", "casual"),
    ("night_fish_landing", "fisher_heng", "fisher_to_crew", "crew_to_fisher", "casual"),
    ("pepper_yard", "grower_mali", "grower_to_helper", "helper_to_grower", "casual"),
    ("radio_booth", "host_mea", "host_to_guest", "guest_to_host", "casual"),
    ("flood_line", "uncle_thon", "elder_to_youth", "youth_to_elder", "casual"),
    ("salt_pan", "salter_pon", "salter_to_helper", "helper_to_salter", "casual"),
    ("kite_workshop", "maker_thy", "maker_to_helper", "helper_to_maker", "casual"),
]
LINES = """
The pyrometer climbed past the cone, so leave this stack inside.
The rim collapsed when I pulled too fast on the wet cylinder.
Score both leather-hard edges or the spout shears off during firing.
I found a hairline crack under the glaze on the blue jar.
Wedge the red clay until the air pockets stop popping in your palms.
The bat slipped off the wheel head because the pins were dusty.
Keep the lid cracked until the steam fades, then drop it for the soak.
This slip beads on the bisque. Should I wipe the dust before a second coat?
Trim the foot ring thinner. The bowl rocks on the kiln shelf.
The handle joint popped in the bisque fire. I forgot to score it.
Use the rib on the inside wall or the cylinder bellies out.
My thumbs left grooves in the neck. Can you show the pull again slower?
The cones are touching. That shelf is done and the next one waits.
Ash from the saggar speckled the white glaze. I will keep the next load cleaner.
Do not stack bowls lip to lip. A setter tile belongs between them.
The wire cut dragged clay crumbs onto the bat. I wiped them before centering.
This porcelain body is short. Add the feldspar pinch I measured on the card.
The sponge is full of grit. I rinsed it and the water ran gray.
Leave the mug to leather hard before you attach the pulled handle.
The glaze crawled on the shoulder. I think the wax resist reached the lip.
The warp threads crossed at the heddle. Uncross them before you throw the shuttle.
The shuttle bounced out of the shed and the weft looped on the selvedge.
Beat the weft with the reed, not with your palm, or the pick stays loose.
A warp end snapped near the beam. I tied a weaver knot and it held.
Keep the tension even. The left side is bagging and the pattern drifts.
The silk bobbin ran out mid-pick. I stopped rather than weave a gap.
Wind the bobbin tighter. A soft wind makes the weft slub under the reed.
My feet missed the treadle and the shed closed on the shuttle.
Tie the new warp onto the old one so the threading stays in the heddles.
The temple stretcher slipped and the cloth narrowed by a finger.
This gold thread is for the border only. The field stays plain silk.
I counted the picks wrong and the diamond motif shifted one row.
Wax the shuttle nose. It snags the warp when the wood is dry.
The lease sticks tangled behind the castle. I separated them with a bone pick.
Stop if you hear a tick. That is a broken end, not the reed.
I marked the fell line with chalk so the beat stays even.
Roll the cloth beam before the web piles against your stomach.
The dye lot on this skein is darker. I set it aside for the hem band.
Cut the finished length only after I check the motif against the sample card.
My shoulders ache from throwing. May I wind bobbins for a while instead?
This blister pack is the evening dose. The morning pack has the yellow stripe.
The label rubbed off in my bag. Can you read the bottle and write it again?
Shake the suspension until the powder lifts. Then draw it to the marked line.
The child spat the syrup. Is there a tablet I can crush with your say-so?
Do not take the antibiotic with the iron pill. Separate them by two hours.
I missed yesterday. Should I double tonight or just resume the printed schedule?
This inhaler is empty when the counter hits zero. Bring the empty canister back.
The cream burned the rash. I stopped after one smear and washed the spot.
Keep the insulin in the fridge door, not in the freezer shelf.
The dropper touched the table. Do you want me to discard that bottle?
Cut the tablet only on the scored groove. The other half is not a dose.
These capsules stick in my throat. Is a full cup required with each one?
The ointment is for the eyelid rim, not inside the eye. Wash your hands after.
I take the pressure pill at breakfast. The new box says bedtime instead.
Bring the old strips. I need the lot number before I swap the glucometer.
The seal under the cap was already split. I did not open it in the shop.
Store the suppositories below room warmth. The windowsill melts them by noon.
Grandmother cannot swallow the capsule. You said a powder sachet exists for this.
Finish the full course even if the fever drops. Stopping early lets it return.
The measuring spoon in the box is stained. May I use the one from the counter?
Stand on the tape mark. If you lean, the backdrop seam shows behind your ear.
The flash left a white disc in my eyes. Can the next frame be without it?
Chin slightly down. The ceiling light is drawing a shadow under your brow.
I blinked when the strobe popped. Count aloud before the next exposure.
Hold the bouquet at your waist, not at your chin, or it hides the necklace.
The veil caught the fan. I pinned it so the lace stays off the lens.
Look at the reflector, not at me. The catchlight should sit high in the eye.
My collar is crooked on the left. Can you straighten it before the group shot?
The softbox is too close. Step back to the second tape or the highlight blows out.
I need one frame with my grandmother seated and the rest of us standing behind.
Do not squint. The window is bright, so I will pull the curtain halfway.
The stool wobbles. I would rather stand than tip during a long exposure.
Tuck the shirt tail. The mirror behind you will show it in the frame.
There is a speck on the backdrop near my shoulder. It looks like a hole.
Smile with your eyes if your mouth is tired. The camera reads the eyes first.
Can we retake the handshake? I looked down at the certificate instead of at him.
The tripod is on the cable. Step over it or the camera dives when you pass.
I want the scar visible. Do not ask me to hide it with the scarf.
Breathe out before I click. Raised shoulders make the jacket bunch at the neck.
The hairpin is slipping. Give me a second to set it or it shows in the close crop.
The crate of snakehead stays on ice. The mud ones go to the other tub.
This fish still flaps. I will not pack a live one under the crushed ice.
Sort the prawns by size. The small grade is for drying, the large grade for the pot.
The weighing pan is wet and the numbers jump. Wipe it before we weigh the basket.
Leave the gills in until the buyer looks. Cut fish sells cheaper at this landing.
A ray barb stuck my boot. I need the pliers from the bow before I pull it.
The outboard coughed on the way in. Tie us to the inner post, not the channel edge.
The net came up heavy with weed. I shook it over the side before the fish hit the deck.
Count the squid by the tub, not by guess. The buyer argues when the tally is soft.
Ice water is in the blue jug. The clear jug is drinking water for the crew.
Do not stand on the gunwale. The wake from that passing hull rocks us.
The hook is through the lip, not the gut. I can release this one if you say.
Pack the crabs with damp cloth, not with ice directly, or they die before market.
The float line tangled in the prop. I cut only the snarled span and kept the rest.
Rinse the blood off the cutting board into the bucket. The river takes nothing from this deck.
My gloves are slick with scales. I will borrow the spare pair on the nail.
The auction starts when the horn sounds. Have the snakehead crate at the front.
A buyer wants the fish gutted. I told him we sell them whole at this hour.
Coil the spare net off the walkway. Someone will trip when the lamps swing.
The bilge alarm light is red. I will bail with the scoop until you check the fuse.
Turn the red berries on the mat. The ones in the shade are still pale.
I raked the green clusters to the edge. They need another sunny day.
Do not sprinkle water on the drying pepper. Moisture invites mold on the skins.
Birds are on the far mat. I can string the shiny ribbon if you have it.
Bag the fully black pepper separately. The red stays for the fresh order.
The tarp blew back and dusted the berries. I shook it off before the stain set.
Stack the dried sacks on the pallet, off the soil, so damp does not climb.
A sack split at the seam. I caught most of the peppercorns in the basin.
Wear the gloves. The fresh spikes sting and the sting lasts past lunch.
I marked the white sack as seed stock and the striped sack as sale.
The mill wants the berries before dusk. Cover the mat if those clouds thicken.
I found mold on one cluster. I pulled it so the mat does not share the spot.
Rake with the grain of the mat. A hard rake tears the berries and wastes the batch.
The afternoon sun left the center hot and the corner cool. I rotated the trays.
Tie the sack mouths with the red cord. The black cord means it is not dry enough.
A goat got past the fence and sniffed the mat. I chased it before it tasted the rows.
Spread the berries one layer deep. Piled fruit steams and turns dull.
My basket has stems in it. I will pick them out before you weigh.
Call me if the mat smokes. Pepper that hot is scorching, not drying.
I saved a handful of the brightest berries in a jar for grandmother's soup.
Your mouth is too close to the mic. The breath pops on every word.
The headphones picked up a horn. Should we pause this segment?
Wait for my cue before you answer. The station jingle is still rolling.
The script page is out of order. The flood question comes before the market prices.
Give the guest the second pair of headphones. She cannot hear her own level.
I stumbled on the commune name. Can we record that sentence once more?
Slide the fader down when you cough. The mic stays live between songs.
There is a hum when the fan starts. I can switch the fan off during the interview.
Read the names slowly. Listeners write them down and a rushed name becomes another person.
My chair squeaks. I will stand for this break so the noise stays out of the take.
We have thirty seconds of music bed. Tell the recipe tip and then stop.
I said grams and the card says spoons. Which measure should I speak on air?
Do not tap the table. It thumps through the mic like a second drum.
The caller is faint. I raised the input and the hiss climbed with the voice.
Introduce yourself with the program name first. People tune in halfway through.
I brought the field recording of the frogs. It can sit under the closing credits.
Keep the paper still. A rustle next to the mic becomes thunder on the speaker.
The red light is on. I will whisper to you instead of speaking across the guest.
After the song, thank the band by name and then open the lines for requests.
I lost my place in the cue sheet. Point to the line and I will pick it up.
Pass the tied sacks from the truck bed. Do not throw them or they burst.
The floodwater is at the second step. I started the wall where the gate dips.
Stomp each sack flat before the next layer. Gaps let the seep through.
My boots are full. I can keep passing sacks if someone else stands in the seep.
The discharge pipe jumped the bank. Weight it with a sack so it stays in the low spot.
Sand is running out at this pile. The next pile is behind the school wall.
Children stay on the dry porch. This line is for people who can lift a sack.
I saw the waterline climb a brick while we talked. We should add a layer now.
Tie the sacks shut with two wraps. A loose mouth dumps sand in the road.
The current tugged a sack off the end. I pinned it with the iron rod from the cart.
Lights on the yellow rope mean the drop. Do not step past that rope.
I brought dry rice bundles for the families on the porch. They are under the blue sheet.
When the siren repeats, we move the line back. One long tone means it is over.
The plastic sheet blew off the sand pile. I weighted the corners with loose bricks.
Hands on the sack corners, lift together. A twisted back stops you for the rest of the day.
I can still lift. The twist was a warning, not an injury, and I changed sides.
Fill from the dry sand, not the mud at the bottom. Mud sacks slide when stacked.
The weather desk said the crest arrives near midnight. I told the porch to sleep in shifts.
Leave a gap at the doorway so the family can still carry the baby out.
I marked the waterline with charcoal on the post. If it rises past the mark, call you.
Rake the crystals toward the pan center before the afternoon wind picks them up.
The brine in this pan is cloudy. I think the ditch mud leaked through the bund.
Do not walk in the fresh crystals. Your footprints stain the white and the buyer notices.
A crab walked into the shallow pan. I lifted it out before it fouled the skim.
The wooden rake lost a tooth. Use the spare rake on the north pan only.
Salt dust is in my eyes. I need the clean water jug, not the brine ladle.
Harvest only the crust that squeaks under the rake. The wet crust stays another day.
The bund leaked on the east side. I packed clay into the cut and the level held.
Wear the cloth over your nose. The noon glare off the pans burns the eyes and the throat.
I stacked the salt sacks on the raised boards. The ground under them was damp.
The storage shed door sticks. Lift it by the crossbar, not by the latch.
A hole in the basket let fine salt trail behind me. I lined it with the spare cloth.
Stop the inflow at the sluice. This pan is deep enough and more water slows the set.
The sluice board is swollen and will not seat. I can plane the edge after the pan rests.
Bag only after the salt cools. Warm sacks sweat and the crust clumps again.
I tasted a pinch and it is sharp, not bitter. Is this pan ready for the sack?
The cloud bank is coming from the sea. Pull the covers over the finished pans first.
My rake handle split. I lashed it with cord and it will do until the wood truck returns.
Children may watch from the path. The pan crust cuts bare feet like glass.
I hung the wet cloths on the bamboo rail. Tell me if the salt smell means they need another rinse.
The bamboo spar has a knot where the bridle ties. Move the knot off the center.
The tissue tore at the nose. I can patch it with the lighter scrap if the glue is still tacky.
Bow the cross spar with the string on the back. A flat kite will not climb.
The tail is too short and the kite spins. I will add a ribbon span before we launch.
Hold the spool and walk the line out. Do not let it run through your fingers.
The wind dropped and the kite sat in the tree. I can climb if you steady the trunk.
The bridle point is high, so the kite dives. Slide the knot a thumb toward the tail.
My line burned a groove in my finger. I will wear the leather tab for the next launch.
Check the spine for a crack before it flies. A cracked spine folds in a gust.
The paint on the eyes smeared. I can redraw them after the glue dries.
Stand upwind of me when you launch. The kite will climb over your hands, not into your face.
I tied the bridle too short on the left and the kite pulls sideways.
The flying line has a knot mid-span. Untie it or the knot will catch the bridle ring.
A child ran under the kite and I spilled the spool. Nobody was hit.
Cut the tissue with the pattern board, not freehand, or the wings come out uneven.
The glue pot skinned over. I stirred it and the brush flows again.
Launch when the grass bends one way. Gusts from two ways will loop the line around you.
I brought the spare tails in the tube. The red one is longer than the blue one.
Reel in if the kite grows small and starts to wink. That height is enough for today.
My wrist is sore from the pull. I can mind the spool if you fly the next one.
""".strip().splitlines()


def _gate():
    spec = importlib.util.spec_from_file_location("spoken_write_train_next", GATE)
    if spec is None or spec.loader is None:
        raise SystemExit("could not load the prior distinctness gate")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _drafts() -> list[dict]:
    if len(LINES) != 200:
        raise SystemExit(f"expected 200 lines, got {len(LINES)}")
    if len(BLOCKS) != 10:
        raise SystemExit("expected 10 situation blocks")
    drafts = []
    for block_index, (setting, expert, rel_out, rel_back, register) in enumerate(BLOCKS):
        for offset in range(20):
            helper = HELPERS[offset // 2]
            expert_speaks = offset % 2 == 0
            drafts.append({
                "kind": "new_situation",
                "emotion": EMOTIONS[offset],
                "speaker_id": expert if expert_speaks else helper,
                "listener_id": helper if expert_speaks else expert,
                "relationship": rel_out if expert_speaks else rel_back,
                "register": register,
                "setting": setting,
                "category": setting,
                "source_text": LINES[block_index * 20 + offset].strip(),
            })
    return drafts


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
            "source_file": "data/khmer_spoken/workspace/spoken_train_next2.jsonl",
            "licence": None,
            "not_for_gold": True,
            "not_for_weight_training": True,
            "locked_from_training": False,
            "scale_pool": "train_next2",
            "setting": draft["setting"],
            "expansion": "kp-2201-kp-2400",
            "created_on": "2026-10-27",
            "situation_kind": draft["kind"],
            "holdout": False,
            "human": False,
            "note": (
                "Synthetic draft. Distinct from kp-001 through kp-2200. "
                "Licence unknown. Not gold. Not human. Not a weight update."
            ),
        },
        "schema_version": SCHEMA_VERSION,
    }


def _load_existing(gate) -> tuple[list[dict], set[str], list[set[str]], set[tuple[str, ...]], int]:
    scale_rows = [json.loads(line) for line in SCALE.read_text(encoding="utf-8").splitlines() if line.strip()]
    prior_rows = [json.loads(line) for line in PRIOR.read_text(encoding="utf-8").splitlines() if line.strip()]
    if [row["id"] for row in scale_rows] != [f"kp-{index:03d}" for index in range(1, 2001)]:
        raise SystemExit("spoken_scale ids are not kp-001 through kp-2000")
    if [row["id"] for row in prior_rows] != [f"kp-{index:04d}" for index in range(2001, 2201)]:
        raise SystemExit("spoken_train_next ids are not kp-2001 through kp-2200")
    holdout_filled = 0
    for row in scale_rows:
        number = int(str(row["id"]).split("-")[1])
        if 1001 <= number <= 2000 and any(
            str((cand or {}).get("text") or "").strip() for cand in (row.get("candidates") or [])
        ):
            holdout_filled += 1
    rows = scale_rows + prior_rows
    norms = {gate._norm(row["source_text"]) for row in rows}
    content = [gate._content(row["source_text"]) for row in rows]
    grams: set[tuple[str, ...]] = set()
    for row in rows:
        grams |= gate._grams(row["source_text"])
    return rows, norms, content, grams, holdout_filled


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    gate = _gate()
    scale_before = hashlib.sha256(SCALE.read_bytes()).hexdigest()
    prior_before = hashlib.sha256(PRIOR.read_bytes()).hexdigest()
    _, norms, content, grams, holdout_filled = _load_existing(gate)
    drafts = _drafts()
    problems = gate._reject(drafts, norms, content, grams)
    if problems:
        print(f"REJECT {len(problems)}")
        for item in problems[:40]:
            print(item)
        raise SystemExit("new rows are not distinct enough; nothing written")
    built = [_row(2200 + index, draft) for index, draft in enumerate(drafts, start=1)]
    if [row["id"] for row in built] != [f"kp-{index:04d}" for index in range(2201, 2401)]:
        raise SystemExit("ids are not kp-2201 through kp-2400")
    for row in built:
        if row["origin"] in {"human_authored", "human_reviewed", "human", "gold"}:
            raise SystemExit(f"{row['id']} origin is forbidden")
        if row["review_status"] != "pending_native_review" or row["license_type"] != "unknown":
            raise SystemExit(f"{row['id']} review or licence is wrong")
        if row["verified_by"] or row["approved_text"] or row["candidates"]:
            raise SystemExit(f"{row['id']} looks approved or filled")
        if row["metadata"].get("human") is not False or row["metadata"].get("not_for_gold") is not True:
            raise SystemExit(f"{row['id']} is marked human or gold")
        number = int(row["id"].split("-")[1])
        if 1001 <= number <= 2000:
            raise SystemExit("holdout id in the new file")
    lines = [json.dumps(row, ensure_ascii=False) for row in built]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(OUT.suffix + ".tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(tmp, OUT)
    scale_after = hashlib.sha256(SCALE.read_bytes()).hexdigest()
    prior_after = hashlib.sha256(PRIOR.read_bytes()).hexdigest()
    if scale_after != scale_before or prior_after != prior_before:
        raise SystemExit("a compared source file changed during the write")
    if holdout_filled != 0:
        raise SystemExit("holdout_filled is not 0")
    settings = Counter(draft["setting"] for draft in drafts)
    print(json.dumps({
        "wrote": str(OUT.relative_to(ROOT)),
        "rows": len(built),
        "id_first": built[0]["id"],
        "id_last": built[-1]["id"],
        "settings": dict(settings),
        "licence": "unknown",
        "review_status": "pending_native_review",
        "origin": "synthetic",
        "human": False,
        "gold": False,
        "distinct_against": "kp-001–kp-2200",
        "holdout_filled_on_scale": holdout_filled,
        "scale_sha256_unchanged": scale_after,
        "train_next_sha256_unchanged": prior_after,
        "weights_started": False,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
