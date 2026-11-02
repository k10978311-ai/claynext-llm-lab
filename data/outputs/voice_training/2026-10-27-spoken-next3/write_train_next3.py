"""Write kp-2401–kp-2600 source rows into a new train-pool file.

Reads spoken_scale.jsonl, spoken_train_next.jsonl, and spoken_train_next2.jsonl
only to reject duplicate source text. Does not write those files, does not
fill candidates, and does not start a trainer.

The refusal is the same gate as write_train_next.py: exact normalized copies,
content-word overlap at or above 0.42, and shared content 5-grams. This pass
applies that gate to kp-001–kp-2400 and inside the new file.
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
PRIOR2 = ROOT / "data/khmer_spoken/workspace/spoken_train_next2.jsonl"
OUT = ROOT / "data/khmer_spoken/workspace/spoken_train_next3.jsonl"
GATE = ROOT / "data/outputs/voice_training/2026-10-26-spoken-next/write_train_next.py"

LICENSE_NOTES = (
    "Synthetic spoken-dialogue draft for the train pool after kp-2400. "
    "Original English line, checked against kp-001 through kp-2400. "
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
    ("apiary_yard", "beekeeper_sovan", "beekeeper_to_helper", "helper_to_beekeeper", "casual"),
    ("dental_chair", "dentist_roth", "dentist_to_patient", "patient_to_dentist", "formal"),
    ("locksmith_bench", "smith_kea", "smith_to_customer", "customer_to_smith", "casual"),
    ("shadow_puppet", "puppeteer_nary", "puppeteer_to_assistant", "assistant_to_puppeteer", "casual"),
    ("rubber_grove", "tapper_mom", "tapper_to_helper", "helper_to_tapper", "casual"),
    ("ice_plant", "icemaker_phan", "icemaker_to_helper", "helper_to_icemaker", "casual"),
    ("goldsmith_bench", "goldsmith_vinh", "goldsmith_to_apprentice", "apprentice_to_goldsmith", "casual"),
    ("weather_hut", "observer_chea", "observer_to_assistant", "assistant_to_observer", "formal"),
    ("lotus_pond", "picker_sreypov", "picker_to_helper", "helper_to_picker", "casual"),
    ("cyclo_stand", "driver_kun", "driver_to_attendant", "attendant_to_driver", "casual"),
]
LINES = """
Smoke the hive entrance reducer before lifting this outer cover.
Brood occupies the middle frames, so those stay in the brood box.
A queen cell dangles under the bottom bar on frame seven.
My veil zipper caught the collar. Hold the frame while I unstick the mesh.
Propolis sealed the inner cover. I ran the hive tool along that seam.
Drones are crowding the landing board. This looks like a seasonal eviction.
That honey super is heavy with nectar. Grip the handholds, never the top bars.
Fresh eggs show in the lower chamber. This colony still has a laying queen.
Syrup from the feeder ran down the hive stand and ants found the drip.
The wax foundation bowed. Swap it for a flat sheet from the spare crate.
A swarm settled on the mango limb. Fetch the extra box and an old bedsheet.
A tear at my glove thumb let a sting through. I need the spare gloves.
Uncap the white cappings only. Open nectar cells remain with the colony.
The honey extractor shakes when baskets are lopsided. Match the frame weights first.
Foragers arriving now carry orange pollen. The tamarind flowers must be open.
Narrow the entrance to a single bee space tonight. Wasps were scouting at dusk.
Use the soft bee brush on this comb. Flicking them with fingers angers the cluster.
Burlap in the smoker died. Relight the canister before we open the next colony.
Dot the queen with green paint. Green is this year's mark, and blue was last year.
Hang the wet extracted frames in the moth-proof shed or wax moths will claim them.
This molar has a shadow on the bitewing. I want a second film from the other angle.
The suction tip is bumping my tongue. Rest it against the cheek instead.
Numbness should reach the lower lip. Tell me when that lip feels thick.
I will place a rubber dam so the tooth stays dry during the filling.
Bite together gently on the blue paper. I am checking the new crown height.
Rinse and spit into the bowl. The silver filling tastes metallic for an hour.
The temporary crown popped off the back tooth while I ate sticky rice.
A clamp for the dam is pinching my gum. Seat it a little lower on that tooth.
Floss between these two teeth catches and shreds. Something sharp is on the filling edge.
The explorer sticks in a groove on the upper left. That groove needs a small filling.
Alginate for the impression sets fast. Keep your teeth together until I say release.
My jaw aches from staying open. May I close for a moment before the next drill.
Shade tab B2 matches the front tooth. I will order the crown in that shade.
Gauze stays over the extraction site for twenty minutes. Avoid chewing on that side.
The polisher spatters. I am covering your eyes, and you can hold the suction.
Cold water on this tooth lingers as pain. That nerve may need further care.
I brought the night guard. It feels tight on the left canine after one week.
The x-ray sensor is bulky. Bite the tab, not the cord, and hold perfectly still.
Numbness is fading unevenly. The tongue woke up and the lip is still dull.
Schedule the crown cementation for Thursday. The lab needs two working days.
This key blank is too thick for the keyway. I need the narrower brass blank.
The plug will not turn after the third pin. A spool pin is catching the shear line.
I cut the code from the card, and the depths match the original key.
Your padlock shackle is bent. A new cylinder will not straighten that shackle.
Hold the tension wrench lightly. Heavy tension hides the pin clicks.
The wafer sidebar is worn. I can rekey the cylinder, but the sidebar still drags.
Someone filed this key into a ramp. I will not copy a key that looks improvised.
The bible screws are stripped. I am moving the pins into a replacement housing.
Master pins in this cylinder allow two keys. Tell me if the second key should keep working.
Graphite, not oil, belongs in this keyway. Oil turns dust into a paste.
The cam on the back of the plug is loose. The tailpiece screws need a tighten.
I decoded the cuts with the depth gauge. Cut three is shallower than the card says.
This mortise cylinder has the wrong thread for your hardware. I can order the matching one.
The pick is hanging on a serrated pin. Reset and start from the back of the plug.
Your spare key opens the knob but not the deadlatch. They are pinned differently.
I stamped the key head with your initials. The cuts themselves are unchanged.
A broken key tip is stuck in the plug. I will extract it with the spiral tool.
The pinning kit is missing a thin driver. I can finish with the next size if you accept a tighter turn.
Do not force the key upward. Lift it level or the first pin stacks.
Come back at four for the cut keys. I still have two cylinders to rekey before yours.
The oil lamp behind the screen is smoking. Trim the wick before the hide yellows.
This buffalo-hide figure has a cracked elbow joint. I will stitch it with the fine rattan.
Punch the eye holes smaller. A wide eye reads as a clown from the third row.
The prince rod crosses the demon rod. Swap hands so the demon stays stage left.
Dye on the new hide is still damp. If we perform tonight the red will smear on the screen.
Gong cue comes before the narrator speaks. I missed it and the scene started late.
Hold the screen frame steady. When it shakes, every silhouette wobbles.
The flicker from that lamp throws two noses on the queen figure. Move the flame back.
I tied the shoulder string too short. The arm cannot lift for the blessing gesture.
Children in the front are touching the screen. Ask them to sit behind the rope.
The chorus chant is early. Wait for the hide to reach center before the verse starts.
My wrist hurts from the heavy demon. I can work the smaller attendant figure for this scene.
A tear near the crown lets light through. Patch it with scrap hide from the tin.
The story calls for the forest crossing now. Hand me the tree panel, not the palace panel.
Oil spit hit the screen. I will wipe it after this scene so the cloth does not stain.
The narrator lost the line about the hermit. Point to the cue card on the stand.
These rods click when they touch. Wrap the crossing point with the cloth tape.
Set the spare lamp where I can reach it. If this flame dies, the show goes black.
The audience laughed at the demon walk. Keep that slow step for the next performance.
Roll the hides with the painted faces outward. Inward rolls crack the pigment.
This tapping panel is too deep. You cut into the cambium and the tree will scar.
The latex cup overflowed overnight. Empty it into the bucket before the drip skins over.
Start the half-spiral at the left rib and slope down toward the spout.
A fresh cut should weep within minutes. This tree is dry, so skip it and mark the bark.
Formic acid in the coagulating tray is low. Add the measured cap, not a splash.
The sheet roller is sticky. Dust it with rice bran before the next coagulum goes through.
Smokehouse racks are full. Hang the new sheets on the upper poles where the air is hotter.
My tapping knife slipped and nicked the groove above the prior cut. I stopped immediately.
Virgin bark on the high panel stays untouched. We only reopen the rested side today.
Ants are farming the spout. Wipe the cup rim or they contaminate the latex.
Grade these sheets by color. Pale ones go in the export bundle, and dark ones stay local.
Rain filled the latex cups. Pour that watery latex away. It will not coagulate cleanly.
The task marks on this row are confusing. Repaint the tree numbers before the buyer walks it.
I smelled ammonia near the storage drums. Check the lid seals before we add today's collection.
The spout nail is loose and latex runs down the bark. Reset the nail under the cut.
Wear the headlamp. The pre-dawn round starts while the cuts are still wet and hard to see.
This tree yield dropped after the deep cut. Leave it untapped for the rest of the month.
Coagulum in the bucket already formed a skin. Stir the edges in so the lump stays one mass.
The buyer wants rubber sheets, not cup lump. Press this batch through the roller before noon.
Lay the dried sheets on the bamboo platform. Soil contact spots them with mold by evening.
The can molds are still soft at the core. Leave them in the bath another twenty minutes.
Hoist this frozen block by the center eye. A side lift cracks it on the dock.
Sawdust in the bunker is damp. Dry sawdust keeps the blocks from welding together.
The ammonia compressor is knocking. Shut the suction valve and call me before any restart.
Score the frozen block along the chalk line. The bar splits cleanly only on that groove.
A thaw puddle is spreading under can twelve. That can has a pinhole and must come out.
Crusher teeth are packed with shards. Clear them or the flake size comes out uneven.
Tickets for the morning delivery are short two blocks. Recount the truck before it leaves the yard.
Wear the dry gloves at the hoist. Wet canvas freezes to the block and tears skin.
The cold-room door seal is torn. Warm air is frosting the coil beside the entrance.
Defrost water from the coil missed the drain and sheeted across the walkway.
This frozen block weighs light on the scale. It froze with a hollow core and the buyer will reject it.
The saltwater bath temperature climbed. I logged the gauge and slowed the harvest.
Stack outgoing blocks on the timber skids. Concrete pulls heat and rounds the corners.
The crane hook latch is sticky. Oil it or a block can slip over the dock edge.
Night shift left the agitator off. The bath stratified and the far cans froze late.
I chipped a corner while sliding a block onto the cart. Note it as a broken piece, not a full unit.
Market buyers want crushed frozen pieces for the fish stalls. Whole blocks stay for the clinic coolers.
The harvest bar bent. Use the spare bar on the small cans only until the welder returns.
Shut the plant if the ammonia smell sharpens. That odor means a leak, not a normal coil.
The bezel is too tight for this stone. I will raise it on the mandrel a half size.
Pickle turned the copper red. Rinse the piece in the soda bath before it touches the bench.
Flux bubbled out of the seam. The solder did not flow, so I am reheating more slowly.
Your ring shank is thin at the bottom. I would add metal before setting the stone.
The drawplate scratched this wire. I am switching to the next smaller hole with fresh wax.
Loupe magnification shows a pit in the solder join. I will refill that pit and file it flush.
Anneal the strip until it glows dull red. Quench only after the color leaves.
Hallmark punch belongs inside the band. A punch on the outer face shows when worn.
The pitch bowl is cold and the piece spins. Warm the pitch or the graver skates.
Jump rings for this clasp must be the heavy gauge. The thin ones opened in my test pull.
Liver of sulfur darkened the recesses. Stop now if you want the highlights to stay bright.
Tripoli is still on the bristles. Wash the brush before switching to the rouge.
I dropped a tiny melee stone. Freeze where you stand so we can find the glint on the mat.
The chenier tubing ovaled in the draw. I will anneal and pull it through once more.
This karat stamp does not match the test result. I will not stamp the band until we retest.
Rolling mill gap is uneven. The left edge of the sheet came out thicker.
A file burr is hiding under the prong. I felt it with a fingertip, not with the loupe.
Customers asked for a matte finish. Skip the final rouge and leave the satin from the tripoli.
The torch tip is clogged and the flame forks. I cleared one hole and the flame is single again.
Sweeps from today's bench go in the labeled jar. Floor dirt stays out of that jar.
The wet-bulb wick dried out. Dampen it with distilled water before reading the pair.
Anemometer cups are wobbling on the shaft. I think a grub screw backed out.
The rain-gauge funnel holds a leaf. Empty the leaf, then record what is actually in the bottle.
Barograph trace jumped at two in the morning. Note the jump instead of smoothing the ink line.
Stevenson screen door was ajar. Today's maximum is suspect until we compare the spare thermometer.
Wind vane is stuck pointing east. Tap the mast lightly, and do not spin it.
The sunshine card burned only a short arc. Cloud covered the hill after midmorning.
Minimum thermometer shows a reset. Someone lifted it off the horizontal clips.
Visibility toward the river is one kilometer in haze. Record haze, because the horizon is still a line.
Evaporation pan lost water past the stilling well. I measured the drop and refilled to the pin.
Soil thermometer at ten centimeters reads warmer than the air. I wrote both numbers in the log.
Hygrometer hair element is slack. The calibration screw needs a quarter turn, then we recheck.
Sling the psychrometer in the shade, away from your body, or the dry bulb reads high.
Cloud genus overhead is altocumulus, not cirrus. The elements have shading and flat bases.
Gusts hit thirty on the dial and the cups whined. I logged the peak apart from the ten-minute mean.
The logbook column for pressure uses hectopascals. Leave inches out of that column.
A spider web is across the gauge mouth. Clear it or tomorrow's rainfall number is wrong.
The observer lamp is dim. Replace the bulb before the evening reading, while the scale is still visible.
Fence around the instrument plot is leaning. A leaning fence disturbs the wind at cup height.
I compared the station barometer with the traveling standard. The difference is two tenths, and I noted it.
Lotus seed pods on the far clump are still green. Harvest only the brown receptacles.
Lotus rhizomes in this corner are thick. Cut them underwater so mud stays off the cut face.
Lotus petals for the temple order must be unopened buds. Open blooms bruise in the crate.
A thorn along the lotus stem caught my wrist. I will switch to the long-handled knife.
The skiff is taking water at the stern plug. Bail before we load another lotus bundle.
Floating lotus leaves are hiding the paths. I marked a clear lane with the bamboo poles.
Lotus stamens for the tea buyer go in the cloth bag. Loose stamens stain the petal bundles.
Knee-deep mud sucked my sandal off. I am feeling for it before the next lotus clump.
This lotus receptacle shattered when I twisted. Slice the stem instead of twisting the pod.
Buyer at the landing wants fifty lotus bundles by eight. We have thirty-two counted on the bank.
Rinse the lotus stems in the pond, not in the roadside ditch. The ditch smells of fuel.
A leech is on my calf. Salt is in the tin by the paddle. Pass it without rocking the skiff.
The fiber strings are in the red bucket. Tie ten lotus stems, then one loose wrap for the buyer.
Dawn wind is pushing the skiff into the reeds. Paddle from the bow while I cut lotus.
These lotus buds opened overnight and no longer fit the temple grade. Set them aside for the soup stall.
My knife handle is slick with lotus sap. I wrapped it with the dry rag from the basket.
The crate on the bank is splitting. Line it with broad leaves before stacking lotus buds.
I left the deepest lotus rhizomes. Pulling those would tear the whole mat and next month's flowers.
Call the bundle number each time one lands in the crate. Yesterday two bunches went missing in the tally.
Call me if the skiff drifts toward the channel. The current there is stronger than it looks.
The passenger awning rib is bent. Riders hit their heads on the low side of the cyclo.
Fare card says four thousand to the school gate. Do not invent a rain surcharge.
Pedal crank on the left is loose. The cotter pin sheared and a spare sits in the pouch.
Hood cloth tore along the rear seam. Safety-pin it until the stitcher opens.
This parcel is wider than the footboard. Lash it to the cyclo frame, not across the rider's knees.
Brake rod stretches when the cyclo stops downhill. Adjust the nut before the temple run.
Bell thumb lever sticks. A drop of oil at the pivot, then wipe the excess off the handle.
Queue at the market stand is ours until noon. After noon the other cyclo team takes the shade.
Rain cape is under the seat cushion. Hand it to the rider before the cloud reaches the stand.
Spoke guard is rubbing the cyclo rim. I heard the tick and stopped before a spoke could snap.
Mirror on the left stem shows only my shoulder. Bend the stem until the lane appears.
A child rider needs the extra cushion. The wooden cyclo seat is too deep for short legs.
Chain guard is dented inward. It ticks against the chain on every slow pedal.
I will pedal the clinic fare. You keep the station queue, which pays better in short cyclo hops.
The horn bulb collapsed. Squeeze the replacement I tied under the awning bow.
Footboard bolts are shining where the paint wore away. Tighten them before a heavy rider steps up.
My calf cramped on the bridge slope. Steer this cyclo while I rest the first twenty meters.
Night lamp on the fender points at the sky. Angle it down so the road, not the awning, is lit.
Receipt pad is damp. Write the fare on the dry card in the tin, then copy it when the pad dries.
Park the cyclo under the tamarind, not against the noodle stall. The stall owner complained yesterday.
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
            "source_file": "data/khmer_spoken/workspace/spoken_train_next3.jsonl",
            "licence": None,
            "not_for_gold": True,
            "not_for_weight_training": True,
            "locked_from_training": False,
            "scale_pool": "train_next3",
            "setting": draft["setting"],
            "expansion": "kp-2401-kp-2600",
            "created_on": "2026-10-27",
            "situation_kind": draft["kind"],
            "holdout": False,
            "human": False,
            "note": (
                "Synthetic draft. Distinct from kp-001 through kp-2400. "
                "Licence unknown. Not gold. Not human. Not a weight update."
            ),
        },
        "schema_version": SCHEMA_VERSION,
    }


def _load_existing(gate) -> tuple[list[dict], set[str], list[set[str]], set[tuple[str, ...]], int]:
    scale_rows = [json.loads(line) for line in SCALE.read_text(encoding="utf-8").splitlines() if line.strip()]
    prior_rows = [json.loads(line) for line in PRIOR.read_text(encoding="utf-8").splitlines() if line.strip()]
    prior2_rows = [json.loads(line) for line in PRIOR2.read_text(encoding="utf-8").splitlines() if line.strip()]
    if [row["id"] for row in scale_rows] != [f"kp-{index:03d}" for index in range(1, 2001)]:
        raise SystemExit("spoken_scale ids are not kp-001 through kp-2000")
    if [row["id"] for row in prior_rows] != [f"kp-{index:04d}" for index in range(2001, 2201)]:
        raise SystemExit("spoken_train_next ids are not kp-2001 through kp-2200")
    if [row["id"] for row in prior2_rows] != [f"kp-{index:04d}" for index in range(2201, 2401)]:
        raise SystemExit("spoken_train_next2 ids are not kp-2201 through kp-2400")
    holdout_filled = 0
    for row in scale_rows:
        number = int(str(row["id"]).split("-")[1])
        if 1001 <= number <= 2000 and any(
            str((cand or {}).get("text") or "").strip() for cand in (row.get("candidates") or [])
        ):
            holdout_filled += 1
    rows = scale_rows + prior_rows + prior2_rows
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
    prior2_before = hashlib.sha256(PRIOR2.read_bytes()).hexdigest()
    _, norms, content, grams, holdout_filled = _load_existing(gate)
    drafts = _drafts()
    problems = gate._reject(drafts, norms, content, grams)
    if problems:
        print(f"REJECT {len(problems)}")
        for item in problems[:80]:
            print(item)
        raise SystemExit("new rows are not distinct enough; nothing written")
    built = [_row(2400 + index, draft) for index, draft in enumerate(drafts, start=1)]
    if [row["id"] for row in built] != [f"kp-{index:04d}" for index in range(2401, 2601)]:
        raise SystemExit("ids are not kp-2401 through kp-2600")
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
    prior2_after = hashlib.sha256(PRIOR2.read_bytes()).hexdigest()
    if scale_after != scale_before or prior_after != prior_before or prior2_after != prior2_before:
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
        "distinct_against": "kp-001–kp-2400",
        "holdout_filled_on_scale": holdout_filled,
        "scale_sha256_unchanged": scale_after,
        "train_next_sha256_unchanged": prior_after,
        "train_next2_sha256_unchanged": prior2_after,
        "weights_started": False,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
