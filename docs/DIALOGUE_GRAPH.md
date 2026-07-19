# Opening Dialogue Graph Contract

Status: Gate 2 implementation contract. `STORY_AND_TIMING.md` owns player-facing copy and dramatic order; `DATA_SCHEMAS.md` owns shipped numeric IDs already declared there. This document closes the remaining allocation, graph, acquisition, retry, help, and revisit gaps. A generator must consume the literal rows below. It may not infer a next node, speaker, condition, action, camera, emote, flag, tick count, root, or fallback from row order.

## 1. Literal encoding rules

`DROW` is a documentation macro with these fixed columns:

```c
DROW(symbol,
     dialogue_hex, dialogue_decimal,
     string_hex, string_decimal,
     speaker_id,
     next_dialogue_id, alternate_dialogue_id,
     condition_id, action_list_xref,
     camera_cue_id, emote_id,
     flags, auto_advance_ticks,
     owner_class,
     "exact UTF-8 text")
```

The decimal values are audit mirrors of the hexadecimal values; disagreement is fatal. `next`, `alternate`, `condition`, and `action_list_xref` are literal zero unless a row says otherwise. `action_list_xref` is validation-only: `StoryTriggerBindingDef` remains the sole dispatcher. Text tokens such as `{PLAYER}`, `{A}`, and `{START}` are preserved byte-for-byte until the text packer resolves runtime glyphs. The curly apostrophe, multiplication sign, em dash, and en dash in copy are UTF-8 source characters, not ASCII substitutions.

Speaker IDs are fixed: `0=NONE/UI/Field Relay/object`, `1=PLAYER`, `2=TAVI`, `3=SERA`, `4=OREN`, `5=IVO`, `6=RUSK`, `7=MARA`, `8=JO`, `9=PELL`. Camera cues are `0x8600=UI/NONE`, `0x8601=SIM_COMMS`, `0x8602=ANNEX_GROUP`, `0x8603=OREN`, `0x8604=JO_RELAY`, `0x8605=PELL_RELAY`, `0x8606=RUSK_COURTYARD`, `0x8607=RUSK_FOYER`, `0x8608=ESTATE_STUDY`, `0x8609=ANNEX_RETURN`, `0x860A=HOOK_GROUP`, `0x860B=OPTIONAL_NPC`, `0x860C=EXAMINE_FOCUS`, `0x860D=POST_CHAPTER`, and `0x860E=MAP_UI`. Emotes are `0=NONE`, `1=NEUTRAL`, `2=INSTRUCT`, `3=WARM`, `4=CONCERNED`, `5=ALERT`, `6=APOLOGETIC`, `7=CURIOUS`, `8=FIRM`, `9=RELIEVED`, `10=DRY`, `11=RECORDED_OR_STATIC`.

Flag values are literal: `0x01=SKIPPABLE_TYPING`, `0x02=CHOICE`, `0x04=ONE_SHOT`, `0x08=CLOSE_AFTER`, and `0x10=KEEP_CAMERA`. Owner classes are `ROOT_STORY`, `ROOT_INTERACTION`, `ROOT_RESULT`, `ROOT_TUTORIAL`, `ROOT_UI`, `ROOT_HELP`, `ROOT_OPTIONAL`, `ROOT_EXAMINE`, `CHAIN`, and `CHOICE_TARGET`. They are generator annotations, not runtime flag bits.

All new non-bridge StringIds use the collision-free one-to-one rule `StringId = DialogueId + 0x4000`; every resulting value is still written literally below. The 16 bridge StringIds in `0x6F01..0x6F10` are exceptions already locked by `DATA_SCHEMAS.md` and are reproduced byte-identically.

## 2. Canonical `DialogueNode` rows

### 2.1 Schema-locked bridge rows

These 16 rows are the byte-exact `MANDATORY_BRIDGE_DIALOGUE_NODES` subset. The three foyer-entry rows explicitly use `CAMERA_CUE_RUSK_FOYER (0x8607)`; every other bridge camera and every bridge emote value is literal zero.

```c
DROW(SIM_001,                 0x531C,21276, 0x6F01,28417, 3, 0x5327,0, 0,0,      0,0, 0x01,0, ROOT_STORY,       "Signal is clean. {PLAYER}, take the near pair.")
DROW(SIM_002,                 0x5327,21287, 0x6F02,28418, 3, 0,0,      0,0x4162, 0,0, 0x09,0, CHAIN,            "Two partners. Two commands. Read the field before you move.")
DROW(EXIT_LOCKED_NO_RELAY,    0x5328,21288, 0x6F03,28419, 0, 0,0,      0,0,      0,0, 0x09,0, ROOT_INTERACTION, "A Field Relay is required for desert travel.")
DROW(EXIT_LOCKED_NO_TRACE,    0x5329,21289, 0x6F04,28420, 3, 0,0,      0,0,      0,0, 0x09,0, ROOT_INTERACTION, "Trace Tavi's packet with Pell before you leave.")
DROW(EXIT_READY_001,          0x532A,21290, 0x6F05,28421, 0, 0x5336,0x5337,0,0, 0,0, 0x02,0, ROOT_INTERACTION, "OPEN DESERT MAP?")
DROW(EXIT_READY_OPEN,         0x5336,21302, 0x6F06,28422, 0, 0,0,      0,0x4163, 0,0, 0x08,0, CHOICE_TARGET,    "OPEN MAP")
DROW(EXIT_READY_STAY,         0x5337,21303, 0x6F07,28423, 0, 0,0,      0,0,      0,0, 0x08,0, CHOICE_TARGET,    "STAY")
DROW(EXIT_READY_REPEAT_001,   0x533A,21306, 0x6F0F,28431, 0, 0x533B,0x5337,0,0, 0,0, 0x02,0, ROOT_INTERACTION, "OPEN DESERT MAP?")
DROW(EXIT_READY_REPEAT_OPEN,  0x533B,21307, 0x6F10,28432, 0, 0,0,      0,0x4164, 0,0, 0x08,0, CHOICE_TARGET,    "OPEN MAP")
DROW(SERA_DEPART_001,         0x532B,21291, 0x6F08,28424, 3, 0,0,      0,0x4167, 0,0, 0x0D,0, ROOT_STORY,       "Bring Tavi home. Keep the pair close.")
DROW(RUSK_ENTRY_001,          0x532C,21292, 0x6F09,28425, 6, 0x532D,0, 0,0,      0x8607,0, 0x11,0, ROOT_STORY,       "Tavi is with Ivo in the upper study.")
DROW(RUSK_ENTRY_002,          0x532D,21293, 0x6F0A,28426, 6, 0x532E,0, 0,0,      0x8607,0, 0x11,0, CHAIN,            "The direct stair is jammed by an orrery arm. The hall route is clear.")
DROW(RUSK_ENTRY_003,          0x532E,21294, 0x6F0B,28427, 6, 0,0,      0,0,      0x8607,0, 0x0D,0, CHAIN,            "Touch nothing that hums in three directions.")
DROW(RUSK_EXIT_001,           0x532F,21295, 0x6F0C,28428, 6, 0x5338,0, 0,0,      0,0, 0x11,0, ROOT_INTERACTION, "I will send Ivo's full chart when the bands clear.")
DROW(TAVI_EXIT_001,           0x5338,21304, 0x6F0D,28429, 2, 0,0,      0,0x4165, 0,0, 0x0D,0, CHAIN,            "And I will send Sera a message before I leave anywhere.")
DROW(RETURN_SKIMMER_REPEAT_001,0x5339,21305,0x6F0E,28430,0, 0,0,       0,0x4166, 0,0, 0x09,0, ROOT_INTERACTION, "RETURN TO ANNEX WITH TAVI?")
```

### 2.2 Mandatory story chains

```c
DROW(ANNEX_INTRO_004, 0x5301,21249, 0x9301,37633, 3,0x5302,0,0,0x4151,0x8602,2,0x11,0,CHAIN,"No borrowed strength now. Listen to them, and let them learn you.")
DROW(ANNEX_INTRO_005, 0x5302,21250, 0x9302,37634, 3,0,0,0,0x4152,0x8602,2,0x09,0,CHAIN,"Director Saye wants you upstairs. Take the atrium and use the lift.")
DROW(OREN_003,        0x5303,21251, 0x9303,37635, 4,0x5343,0,0,0x4110,0x8603,2,0x11,0,CHAIN,"Jo finished your Field Relay. Collect it from the lower workshop.")
DROW(JO_RELAY_006,    0x5304,21252, 0x9304,37636, 8,0,0,0,0x4140,0x8604,2,0x09,0,CHAIN,"That packet left the Annex repeater. Pell can read the route header upstairs.")
DROW(SERA_RELAY_002,  0x5305,21253, 0x9305,37637, 3,0x5306,0,0,0x4141,0x8605,8,0x11,0,CHAIN,"{PLAYER}, bring the field pair. Find Tavi; call if the route changes.")
DROW(PELL_TRACE_004,  0x5306,21254, 0x9306,37638, 9,0,0,0,0x4142,0x8605,2,0x09,0,CHAIN,"Estate node is live. The skimmer at the exterior threshold will take you.")
DROW(RUSK_PRE_005,    0x5307,21255, 0x9307,37639, 6,0,0,0,0x4111,0x8606,8,0x09,0,CHAIN,"No? Then show me whose pattern you carry.")
DROW(RUSK_RETRY_001,  0x5308,21256, 0x9308,37640, 6,0,0,0,0x4112,0x8606,8,0x09,0,ROOT_STORY,"We still have an unanswered signal between us.")
DROW(RUSK_RETRY_IMMEDIATE_001,0x5309,21257,0x9309,37641,6,0,0,0,0x4113,0x8606,8,0x09,0,ROOT_STORY,"Ready? Then let the true pattern answer.")
DROW(SERA_RUSK_RETURN_001,0x530A,21258,0x930A,37642,3,0,0,0,0x4161,0x8605,4,0x0D,0,ROOT_STORY,"Regroup. Tavi is safe at the Estate; go back when your pair is ready.")
DROW(RUSK_POST_005,   0x530B,21259, 0x930B,37643, 6,0,0,0,0x4168,0x8606,9,0x09,0,CHAIN,"Your companions are steady. Let me restore them, then I will open the Estate.")
DROW(REUNION_001,     0x530C,21260, 0x930C,37644, 2,0x5365,0,0,0x4158,0x8608,9,0x11,0,ROOT_STORY,"You found me. The Relay works!")
DROW(REUNION_004,     0x530D,21261, 0x930D,37645, 5,0x5367,0,0,0x4159,0x8608,6,0x11,0,CHAIN,"The fault is shared. I confirmed the tag and forgot to confirm the child.")
DROW(REUNION_011,     0x530E,21262, 0x930E,37646, 2,0,0,0,0x415A,0x8608,8,0x09,0,CHAIN,"I will follow. Properly this time.")
DROW(RETURN_005,      0x530F,21263, 0x930F,37647, 4,0x5371,0,0,0x415B,0x8609,10,0x11,0,CHAIN,"Objective resolved. Next time, the calibration tag hides where the map is lit.")
DROW(RETURN_007,      0x5310,21264, 0x9310,37648, 3,0,0,0,0x415C,0x8609,3,0x09,0,CHAIN,"{PLAYER}, you brought Tavi back and kept the pair steady. Well done.")
DROW(HOOK_005,        0x5311,21265, 0x9311,37649, 9,0x5375,0,0,0x415E,0x860A,5,0x11,0,CHAIN,"Then the beacon moved. Twelve kilometers against the wind.")
DROW(HOOK_010,        0x5312,21266, 0x9312,37650, 9,0x5379,0,0,0x415F,0x860A,5,0x11,0,CHAIN,"That pattern is Fractured.")
DROW(HOOK_014,        0x5313,21267, 0x9313,37651, 3,0,0,0,0x4160,0x860A,8,0x09,0,CHAIN,"We find it before the Severance does.")
DROW(POST_OREN_001,   0x5314,21268, 0x9314,37652, 4,0,0,0,0,0x860D,8,0x09,0,ROOT_OPTIONAL,"The opening record is secure. No guesses will become orders.")
DROW(POST_OREN_UNSAVED_001,0x5315,21269,0x9315,37653,4,0,0,0,0,0x860D,8,0x09,0,ROOT_OPTIONAL,"The Relay has not secured this record yet. We will not pretend otherwise.")
DROW(ANNEX_INTRO_001, 0x5316,21270, 0x9316,37654, 3,0x5340,0,0,0,0x8602,1,0x11,0,ROOT_STORY,"Loaned patterns behave beautifully. Real partners have opinions.")
DROW(RUSK_WIN_UI_001, 0x5317,21271, 0x9317,37655, 0,0x535A,0,0,0,0x8600,0,0x10,45,ROOT_RESULT,"FIELD RESONANCE VALIDATED")
DROW(RUSK_LOSE_001,   0x5318,21272, 0x9318,37656, 0,0x5362,0,0,0,0x8600,0,0x10,45,ROOT_RESULT,"YOUR RESONANCE FELL QUIET")
DROW(RUSK_LOSE_CHOICE,0x5319,21273, 0x9319,37657, 0,0x5363,0x5364,0,0,0x8600,0,0x02,0,CHAIN,"Try the encounter again?")
DROW(RETURN_001,      0x531A,21274, 0x931A,37658, 3,0x536E,0,0,0,0x8609,8,0x11,0,ROOT_STORY,"Tavi.")
DROW(HOOK_001,        0x531B,21275, 0x931B,37659, 0,0x5372,0,0,0,0x860A,0,0x10,30,ROOT_STORY,"OBSERVATORY PACKET RESOLVED")
DROW(RUSK_PRE_001,    0x531D,21277, 0x931D,37661, 6,0x5356,0,0,0,0x8606,5,0x11,0,ROOT_STORY,"Stop there. That Relay just answered a cut-wave.")
DROW(OREN_001,        0x531E,21278, 0x931E,37662, 4,0x5342,0,0,0,0x8603,1,0x11,0,ROOT_INTERACTION,"{PLAYER}. Sera says the simulation held.")
DROW(JO_RELAY_001,    0x531F,21279, 0x931F,37663, 8,0x5346,0,0,0,0x8604,10,0x11,0,ROOT_INTERACTION,"There it is. Sandproof, drop-tolerant, and almost Tavi-proof.")
DROW(PELL_TRACE_001,  0x5326,21286, 0x9326,37670, 9,0x534D,0,0,0,0x8605,2,0x11,0,ROOT_INTERACTION,"Send me the header.")
```

### 2.3 Remaining mandatory, map, retry, and post-chapter rows

```c
DROW(ANNEX_INTRO_002,0x5340,21312,0x9340,37696,7,0x5341,0,0,0,0x8602,3,0x11,0,CHAIN,"These two watched every round. They did not agree with every choice.")
DROW(ANNEX_INTRO_003,0x5341,21313,0x9341,37697,3,0x5301,0,0,0,0x8602,3,0x11,0,CHAIN,"Quarrune. Ayselor. This is {PLAYER}.")
DROW(OREN_002,0x5342,21314,0x9342,37698,4,0x5303,0,0,0,0x8603,1,0x11,0,CHAIN,"Your field pair deserves a field instrument.")
DROW(OREN_004,0x5343,21315,0x9343,37699,4,0x5344,0,0,0,0x8603,2,0x11,0,CHAIN,"It carries party records, messages, saves, and the desert map. Learn it before leaving the Annex.")
DROW(OREN_005,0x5344,21316,0x9344,37700,4,0x5345,0,0,0,0x8603,1,0x11,0,CHAIN,"Tavi hid a calibration tag for its first test. The rule was: inside the Annex.")
DROW(OREN_006,0x5345,21317,0x9345,37701,4,0,0,0,0,0x8603,4,0x09,0,CHAIN,"Tavi is late. Retrieve the Relay; the tag will tell us whether to worry.")
DROW(JO_RELAY_002,0x5346,21318,0x9346,37702,8,0x5347,0,0,0,0x8604,2,0x11,0,CHAIN,"Thumb the side latch. If it chirps twice, it trusts you.")
DROW(JO_RELAY_003,0x5347,21319,0x9347,37703,0,0x5348,0,0,0,0x8604,0,0x10,30,CHAIN,"CALLSIGN LINKED: {PLAYER}")
DROW(JO_RELAY_004,0x5348,21320,0x9348,37704,8,0x5349,0,0,0,0x8604,2,0x11,0,CHAIN,"Party on the left. Records on the right. Map stays honest about where you can go.")
DROW(JO_RELAY_005,0x5349,21321,0x9349,37705,0,0x534A,0,0,0,0x8604,0,0x10,30,CHAIN,"1 QUEUED CALIBRATION MESSAGE")
DROW(TAVI_MSG_001,0x534A,21322,0x934A,37706,2,0x534B,0,0,0,0x8604,11,0x11,0,CHAIN,"{PLAYER}! I found a better place for the tag.")
DROW(TAVI_MSG_002,0x534B,21323,0x934B,37707,2,0x534C,0,0,0,0x8604,11,0x11,0,CHAIN,"The roof moves like a metal sky. Ivo says his stars can hear the desert.")
DROW(TAVI_MSG_003,0x534C,21324,0x934C,37708,2,0x5304,0,0,0,0x8604,11,0x11,0,CHAIN,"Come find me before Sera wins hide-and-seek by worrying.")
DROW(PELL_TRACE_002,0x534D,21325,0x934D,37709,9,0x534E,0,0,0,0x8605,2,0x11,0,CHAIN,"Veyra Observatory Estate. Western ridge.")
DROW(PELL_TRACE_003,0x534E,21326,0x934E,37710,9,0x534F,0,0,0,0x8605,4,0x11,0,CHAIN,"The service crawler logged one passenger: Tavi. Arrival confirmed. No return trip.")
DROW(SERA_RELAY_001,0x534F,21327,0x934F,37711,3,0x5305,0,0,0,0x8605,11,0x11,0,CHAIN,"Tavi is safe enough to send jokes, and far enough to come home now.")

DROW(MAP_ANNEX_NAME,0x5350,21328,0x9350,37712,0,0,0,0,0,0x860E,0,0x08,0,ROOT_UI,"MERIDIAN ANNEX")
DROW(MAP_ANNEX_DESC,0x5351,21329,0x9351,37713,0,0,0,0,0,0x860E,0,0x08,0,ROOT_UI,"Research outpost and Resonance clinic — Eastern Basin")
DROW(MAP_ESTATE_NAME,0x5352,21330,0x9352,37714,0,0,0,0,0,0x860E,0,0x08,0,ROOT_UI,"VEYRA ESTATE")
DROW(MAP_ESTATE_DESC,0x5353,21331,0x9353,37715,0,0,0,0,0,0x860E,0,0x08,0,ROOT_UI,"Observatory and independent workshop — Western Ridge")
DROW(MAP_TRAVEL_CONFIRM,0x5354,21332,0x9354,37716,0,0x544E,0x544F,0,0,0x860E,0,0x02,0,ROOT_UI,"Travel to Veyra Observatory Estate?")
DROW(MAP_RETURN_CONFIRM,0x5355,21333,0x9355,37717,0,0x5450,0x5451,0,0,0x860E,0,0x02,0,ROOT_UI,"Travel to Meridian Research Annex?")

DROW(RUSK_PRE_002,0x5356,21334,0x9356,37718,6,0x5357,0,0,0,0x8606,5,0x11,0,CHAIN,"Severance scouts use that band to find what they have broken.")
DROW(SERA_STATIC_001,0x5357,21335,0x9357,37719,3,0x5358,0,0,0,0x8606,11,0x11,0,CHAIN,"Rusk, stand down. That is—")
DROW(RUSK_PRE_003,0x5358,21336,0x9358,37720,6,0x5359,0,0,0,0x8606,8,0x11,0,CHAIN,"A borrowed voice is not clearance.")
DROW(RUSK_PRE_004,0x5359,21337,0x9359,37721,6,0x5307,0,0,0,0x8606,8,0x11,0,CHAIN,"Set the Relay down and step away from the Estate.")
DROW(RUSK_WIN_UI_002,0x535A,21338,0x935A,37722,0,0x535B,0,0,0,0x8600,0,0x10,30,CHAIN,"Quarrune  +25 SYNC")
DROW(RUSK_WIN_UI_003,0x535B,21339,0x935B,37723,0,0x535C,0,0,0,0x8600,0,0x10,30,CHAIN,"Ayselor  +25 SYNC")
DROW(RUSK_WIN_UI_004,0x535C,21340,0x935C,37724,0,0x535D,0,0,0,0x8600,0,0x10,45,CHAIN,"TEAM LINK  1")
DROW(RUSK_POST_001,0x535D,21341,0x935D,37725,6,0x535E,0,0,0,0x8606,5,0x11,0,CHAIN,"Hold. I know that horn lattice.")
DROW(RUSK_POST_002,0x535E,21342,0x935E,37726,6,0x535F,0,0,0,0x8606,9,0x11,0,CHAIN,"Sera's Quarrune. Sera's Ayselor.")
DROW(TAVI_DOOR_001,0x535F,21343,0x935F,37727,2,0x5360,0,0,0,0x8606,11,0x11,0,CHAIN,"{PLAYER}? Did the new Relay work?")
DROW(RUSK_POST_003,0x5360,21344,0x9360,37728,6,0x5361,0,0,0,0x8606,6,0x11,0,CHAIN,"It worked. I did not.")
DROW(RUSK_POST_004,0x5361,21345,0x9361,37729,6,0x530B,0,0,0,0x8606,6,0x11,0,CHAIN,"I mistook your signal for Severance work. I am sorry.")
DROW(RUSK_LOSE_002,0x5362,21346,0x9362,37730,6,0x5319,0,0,0,0x8606,8,0x11,0,CHAIN,"Enough. I will not press a fallen pair.")
DROW(RUSK_LOSE_RETRY,0x5363,21347,0x9363,37731,0,0,0,0,0,0x8600,0,0x08,0,CHOICE_TARGET,"RETRY")
DROW(RUSK_LOSE_RETURN,0x5364,21348,0x9364,37732,0,0,0,0,0,0x8600,0,0x08,0,CHOICE_TARGET,"RETURN TO ANNEX")

DROW(REUNION_002,0x5365,21349,0x9365,37733,2,0x5366,0,0,0,0x8608,6,0x11,0,CHAIN,"I know. The rule was inside the Annex.")
DROW(REUNION_003,0x5366,21350,0x9366,37734,2,0x530D,0,0,0,0x8608,6,0x11,0,CHAIN,"The crawler was leaving, and Ivo's roof really does move. I should have asked.")
DROW(REUNION_005,0x5367,21351,0x9367,37735,5,0x5368,0,0,0,0x8608,7,0x11,0,CHAIN,"Still, your search brought the correct instrument.")
DROW(REUNION_006,0x5368,21352,0x9368,37736,5,0x5369,0,0,0,0x8608,7,0x11,0,CHAIN,"At dusk, my lowest lens heard a star fall upward.")
DROW(REUNION_007,0x5369,21353,0x9369,37737,5,0x536A,0,0,0,0x8608,7,0x11,0,CHAIN,"Not light. A carrier handshake, buried inside a violet shear.")
DROW(REUNION_008,0x536A,21354,0x936A,37738,0,0x536B,0,0,0,0x8608,0,0x10,30,CHAIN,"OBSERVATORY PACKET RECEIVED — ANALYSIS PENDING")
DROW(REUNION_009,0x536B,21355,0x936B,37739,2,0x536C,0,0,0,0x8608,4,0x11,0,CHAIN,"Sera is going to use my entire name.")
DROW(REUNION_010,0x536C,21356,0x936C,37740,5,0x530E,0,0,0,0x8608,10,0x11,0,CHAIN,"Then do not make her spend it twice. Go home together.")
DROW(TAVI_FOLLOW_001,0x536D,21357,0x936D,37741,2,0,0,0,0,0x8608,8,0x09,0,ROOT_INTERACTION,"I am here. Annex first; questions after.")

DROW(RETURN_002,0x536E,21358,0x936E,37742,2,0x536F,0,0,0,0x8609,6,0x11,0,CHAIN,"I left the boundary without asking. I sent the tag, not the plan.")
DROW(RETURN_003,0x536F,21359,0x936F,37743,2,0x5370,0,0,0,0x8609,6,0x11,0,CHAIN,"I am sorry.")
DROW(RETURN_004,0x5370,21360,0x9370,37744,3,0x530F,0,0,0,0x8609,3,0x11,0,CHAIN,"You are home. We can be relieved and still change the rules.")
DROW(RETURN_006,0x5371,21361,0x9371,37745,2,0x5310,0,0,0,0x8609,9,0x11,0,CHAIN,"That is fair.")

DROW(HOOK_002,0x5372,21362,0x9372,37746,9,0x5373,0,0,0,0x860A,5,0x11,0,CHAIN,"Director. Carrier handshake S-04.")
DROW(HOOK_003,0x5373,21363,0x9373,37747,4,0x5374,0,0,0,0x860A,5,0x11,0,CHAIN,"Solace.")
DROW(HOOK_004,0x5374,21364,0x9374,37748,3,0x5311,0,0,0,0x860A,4,0x11,0,CHAIN,"Its emergency beacon fell beyond our last sweep.")
DROW(HOOK_006,0x5375,21365,0x9375,37749,2,0x5376,0,0,0,0x860A,7,0x11,0,CHAIN,"A beacon cannot walk.")
DROW(HOOK_007,0x5376,21366,0x9376,37750,5,0x5377,0,0,0,0x860A,11,0x11,0,CHAIN,"Correct. Something carried the signal—or bent the distance around it.")
DROW(HOOK_008,0x5377,21367,0x9377,37751,3,0x5378,0,0,0,0x860A,5,0x11,0,CHAIN,"Quiet. The pair hear something.")
DROW(HOOK_009,0x5378,21368,0x9378,37752,0,0x5312,0,0,0,0x860A,0,0x10,30,CHAIN,"UNKNOWN RESONANCE RESPONSE")
DROW(HOOK_011,0x5379,21369,0x9379,37753,4,0x537A,0,0,0,0x860A,5,0x11,0,CHAIN,"It is answering Solace.")
DROW(HOOK_012,0x537A,21370,0x937A,37754,2,0x537B,0,0,0,0x860A,7,0x11,0,CHAIN,"Can it hear us?")
DROW(HOOK_013,0x537B,21371,0x937B,37755,3,0x5313,0,0,0,0x860A,8,0x11,0,CHAIN,"Not yet.")

DROW(POST_SERA_001,0x537C,21372,0x937C,37756,3,0,0,0,0,0x860D,3,0x09,0,ROOT_OPTIONAL,"Rest the pair. We move when the signal is understood.")
DROW(POST_TAVI_001,0x537D,21373,0x937D,37757,2,0,0,0,0,0x860D,10,0x09,0,ROOT_OPTIONAL,"Next trip: message first, moving roof second.")
DROW(POST_PELL_001,0x537E,21374,0x937E,37758,9,0,0,0,0,0x860D,7,0x09,0,ROOT_OPTIONAL,"The signal is still moving. The map is not ready to call it a route.")
DROW(POST_RUSK_001,0x537F,21375,0x937F,37759,6,0,0,0,0,0x860D,10,0x09,0,ROOT_OPTIONAL,"The Estate recognizes your pattern. I am improving at that.")
DROW(POST_IVO_001,0x5380,21376,0x9380,37760,5,0,0,0,0,0x860D,10,0x09,0,ROOT_OPTIONAL,"A falling star that climbs is either a discovery or an apology from physics.")
```

### 2.4 First-use help and optional NPC rows

```c
DROW(HELP_MOVE,0x5320,21280,0x9320,37664,0,0,0,0,0,0x8600,0,0x0C,0,ROOT_HELP,"{STICK} MOVE   Hold {B} RUN   {A} INTERACT")
DROW(HELP_CAMERA,0x5321,21281,0x9321,37665,0,0,0,0,0,0x8600,0,0x0C,0,ROOT_HELP,"{C-LEFT}/{C-RIGHT} TURN   HOLD {L}+{C-UP}/{C-DOWN} TILT")
DROW(HELP_PAUSE,0x5322,21282,0x9322,37666,0,0,0,0,0,0x8600,0,0x0C,0,ROOT_HELP,"{START} PAUSE")
DROW(HELP_PARTY,0x5323,21283,0x9323,37667,0,0,0,0,0,0x8600,0,0x0C,0,ROOT_HELP,"View Quarrune and Ayselor under PARTY.")
DROW(HELP_SAVE,0x5324,21284,0x9324,37668,0,0,0,0,0,0x8600,0,0x0C,0,ROOT_HELP,"Record progress from the Field Relay when the area is stable.")
DROW(HELP_MAP,0x5325,21285,0x9325,37669,0,0,0,0,0,0x8600,0,0x0C,0,ROOT_HELP,"Choose a lit destination. Dark horizon marks are not routes.")

DROW(MARA_PRE_001,0x5330,21296,0x9330,37680,7,0,0,0,0,0x860B,7,0x09,0,ROOT_OPTIONAL,"Quarrune pretends not to watch Ayselor. The second you turn away, all six ears follow.")
DROW(MARA_POST_001,0x5331,21297,0x9331,37681,7,0,0,0,0,0x860B,2,0x09,0,ROOT_OPTIONAL,"The pair are healthy. If Rusk gets dramatic, let Quarrune hold the line.")
DROW(JO_PRE_001,0x5332,21298,0x9332,37682,8,0,0,0,0,0x860B,10,0x09,0,ROOT_OPTIONAL,"Your Relay passed the dust box. The dust box did not.")
DROW(JO_POST_001,0x5333,21299,0x9333,37683,8,0,0,0,0,0x860B,10,0x09,0,ROOT_OPTIONAL,"If the map spins, you are holding it upside down. I put the latch on top.")
DROW(PELL_PRE_001,0x5334,21300,0x9334,37684,9,0,0,0,0,0x860B,1,0x09,0,ROOT_OPTIONAL,"Clear weather, quiet bands, one carrier still overdue.")
DROW(PELL_POST_001,0x5335,21301,0x9335,37685,9,0,0,0,0,0x860B,7,0x09,0,ROOT_OPTIONAL,"The Estate signal is odd, not hostile. There is a difference.")
```

### 2.5 Examine rows

Examine persistence is owned by `ExamineOnceRegistryDef`, not `DIALOGUE_ONE_SHOT`; repeat reads show the same row without replaying the first-use object animation/action.

```c
DROW(ESTATE_EX_ORRERY,0x5201,20993,0x9201,37377,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"The brass arm blocks the stair and tracks an object below the horizon.")
DROW(ESTATE_EX_SWITCH_OPEN,0x5202,20994,0x9202,37378,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"The switch rests in its open notch. The stair is clear.")
DROW(ESTATE_EX_ORRERY_OPEN,0x5203,20995,0x9203,37379,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"The brass arm rests above the cleared stair, still tracking below the horizon.")

DROW(ANNEX_EX_SIM,0x5401,21505,0x9401,37889,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"The projected salt basin is gone. Four faint footprints still pulse in the floor.")
DROW(ANNEX_EX_MONITOR,0x5402,21506,0x9402,37890,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"Two clean waveforms overlap, separate, and meet again.")
DROW(ANNEX_EX_SOLACE,0x5403,21507,0x9403,37891,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"A long-range research carrier. Its brass nameplate reads: SOLACE.")
DROW(ANNEX_EX_CLINIC,0x5404,21508,0x9404,37892,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"Warm ceramic nests hold water, mineral blocks, and folded cooling cloth.")
DROW(ANNEX_EX_TOOLWALL,0x5405,21509,0x9405,37893,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"Every tool has a painted outline. Three outlines are Tavi-sized and empty.")
DROW(ANNEX_EX_PLAYER_ROOM,0x5406,21510,0x9406,37894,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"A desert-glass shard, a field notebook, and a space waiting for the Relay.")
DROW(ANNEX_EX_WINDOW,0x5407,21511,0x9407,37895,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"The western ridge cuts a dark tooth into the bright desert.")
DROW(ANNEX_EX_LIFT,0x5408,21512,0x9408,37896,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"The lift plate shows two levels and one very old dent.")
DROW(ESTATE_EX_FOUNTAIN,0x5409,21513,0x9409,37897,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"Copper petals turn falling water into a slow blue spark.")
DROW(ESTATE_EX_WEATHERVANE,0x540A,21514,0x940A,37898,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"The vane points toward the wind, then argues with itself.")
DROW(ESTATE_EX_TRACKS,0x540B,21515,0x940B,37899,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"Fresh, narrow footprints lead from the crawler stop to the front door.")
DROW(ESTATE_EX_GARDEN,0x540C,21516,0x940C,37900,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"Shade cloth keeps silverleaf and red needlegrass cool.")
DROW(ESTATE_EX_DOME,0x540D,21517,0x940D,37901,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"The roof is open by one handspan. Something inside keeps ticking.")
DROW(ESTATE_EX_PORTRAIT,0x540E,21518,0x940E,37902,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"Ivo and Rusk stand beside a younger observatory dome. Both are pretending not to smile.")
DROW(ESTATE_EX_COMPASS,0x540F,21519,0x940F,37903,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"Every needle points at a different interesting mistake.")
DROW(ESTATE_EX_WALKDESK,0x5410,21520,0x9410,37904,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"Four padded feet lift in sequence. The desk has traveled almost a meter.")
DROW(ESTATE_EX_BOTTLESTAR,0x5411,21521,0x9411,37905,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"A warm point of light circles the glass whenever Ayselor passes.")
DROW(ESTATE_EX_RAINCLOCK,0x5412,21522,0x9412,37906,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"It measures the time since rain. The smallest hand has not moved.")
DROW(ESTATE_EX_LOGBOOK,0x5413,21523,0x9413,37907,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"One line is underlined twice: A FALLING SIGNAL CAN STILL BE MOVING.")
DROW(ESTATE_EX_TELESCOPE,0x5414,21524,0x9414,37908,0,0,0,0,0,0x860C,0,0x09,0,ROOT_EXAMINE,"The eyepiece is warm. Violet dust clings to the outer ring.")
```

### 2.6 Tutorial and simulation result rows

The fixed `TUTORIAL_GATE*_INSTRUCTION/REPEAT` constants are aliases of the canonical symbols at `0x5501..0x550A`; they are not duplicate nodes. `SIM_G1_REPEAT`, `SIM_G2_REPEAT`, and `SIM_G4_REPEAT` are derived repeat pages whose text is an exact duplicate of the cited master line, with a distinct DialogueId and StringId so tutorial owners never create ID aliases.

```c
DROW(SIM_G1_HP,0x5501,21761,0x9501,38145,3,0x5510,0,0,0,0x8601,2,0x11,0,ROOT_TUTORIAL,"HP shows who can still act. At zero, an Echoform leaves the field.")
DROW(SIM_G1_REPEAT,0x5502,21762,0x9502,38146,3,0,0,0,0,0x8601,2,0x09,0,ROOT_TUTORIAL,"Choose a move for each partner, then choose a legal target.")
DROW(SIM_G2_001,0x5503,21763,0x9503,38147,3,0x5513,0,0,0,0x8601,2,0x11,0,ROOT_TUTORIAL,"Affinity changes force, not permission. Check the marks beside each target.")
DROW(SIM_G2_REPEAT,0x5504,21764,0x9504,38148,3,0,0,0,0,0x8601,2,0x09,0,ROOT_TUTORIAL,"Affinity changes force, not permission. Check the marks beside each target.")
DROW(SIM_G3_001,0x5505,21765,0x9505,38149,3,0x5516,0,0,0,0x8601,2,0x11,0,ROOT_TUTORIAL,"Power is only half a pair. Use one support move this round.")
DROW(SIM_G3_REPEAT,0x5506,21766,0x9506,38150,3,0,0,0,0,0x8601,2,0x09,0,ROOT_TUTORIAL,"Try one marked SUPPORT move. Your other command is still yours.")
DROW(SIM_G4_001,0x5507,21767,0x9507,38151,3,0x5517,0,0,0,0x8601,2,0x11,0,ROOT_TUTORIAL,"That shared signal is Resonance. Cooperation builds it faster than repetition.")
DROW(SIM_G4_REPEAT,0x5508,21768,0x9508,38152,3,0,0,0,0,0x8601,2,0x09,0,ROOT_TUTORIAL,"Give one partner an opening. Let the other use it.")
DROW(SIM_G5_001,0x5509,21769,0x9509,38153,3,0,0,0,0,0x8601,2,0x09,0,ROOT_TUTORIAL,"Full Resonance opens a duo finisher. Choose SUNLINE CASCADE.")
DROW(SIM_G5_REPEAT,0x550A,21770,0x950A,38154,3,0,0,0,0,0x8601,2,0x09,0,ROOT_TUTORIAL,"The pattern will hold. Use it when you are ready.")

DROW(SIM_G1_001,0x5510,21776,0x9510,38160,3,0x5511,0,0,0,0x8601,2,0x11,0,CHAIN,"Choose a move for each partner, then choose a legal target.")
DROW(SIM_G1_INFO,0x5511,21777,0x9511,38161,0,0,0,0,0,0x8600,0,0x08,0,CHAIN,"{Z} MOVE INFO   {A} SELECT   {B} BACK")
DROW(SIM_G1_DONE,0x5512,21778,0x9512,38162,3,0,0,0,0,0x8601,3,0x09,0,ROOT_TUTORIAL,"Good. The queue is built only after both commands are sound.")
DROW(SIM_G2_002,0x5513,21779,0x9513,38163,3,0,0,0,0,0x8601,2,0x09,0,CHAIN,"Priority marks resolve first. Speed orders matching marks. If a target falls first, that queued move safely drops.")
DROW(SIM_EFFECT_STRONG,0x5514,21780,0x9514,38164,0,0,0,0,0,0x8600,0,0x08,45,ROOT_TUTORIAL,"STRONG — 1.5× affinity force")
DROW(SIM_EFFECT_RESIST,0x5515,21781,0x9515,38165,0,0,0,0,0,0x8600,0,0x08,45,ROOT_TUTORIAL,"RESISTED — 0.75× affinity force")
DROW(SIM_G3_002,0x5516,21782,0x9516,38166,3,0,0,0,0,0x8601,2,0x09,0,CHAIN,"Staggered slows the next action, then clears. Some field moves can clear it early.")
DROW(SIM_G4_002,0x5517,21783,0x9517,38167,3,0,0,0,0,0x8601,2,0x09,0,CHAIN,"Give one partner an opening. Let the other use it.")
DROW(SIM_G4_FULL,0x5518,21784,0x9518,38168,3,0,0,0,0,0x8601,9,0x09,0,ROOT_TUTORIAL,"Pattern locked. Both partners are ready.")
DROW(SIM_FINISHER_INFO,0x5519,21785,0x9519,38169,0,0,0,0,0,0x8600,0,0x08,0,ROOT_TUTORIAL,"SUNLINE CASCADE — BOTH FOES — REQUIRES BOTH PARTNERS")
DROW(SIM_G5_DONE,0x551A,21786,0x951A,38170,3,0x551B,0,0,0,0x8601,9,0x11,0,ROOT_TUTORIAL,"Stable, readable, and together. Simulation complete.")
DROW(SIM_RESULT_COMPLETE,0x551B,21787,0x951B,38171,0,0,0,0,0,0x8600,0,0x08,60,ROOT_RESULT,"SIMULATION COMPLETE")
DROW(SIM_RESULT_INTERRUPTED,0x551C,21788,0x951C,38172,0,0x551D,0,0,0,0x8600,0,0x10,0,ROOT_RESULT,"SIMULATION INTERRUPTED")
DROW(SIM_RESULT_RESTART,0x551D,21789,0x951D,38173,0,0,0,0,0x4169,0x8600,0,0x08,0,CHOICE_TARGET,"RESTART")
DROW(SIM_RESULT_CALIBRATION_HOLD,0x551E,21790,0x951E,38174,0,0,0,0,0,0x8600,0,0x08,45,ROOT_RESULT,"CALIBRATION HOLD")
```

### 2.7 Process, title, name, loading, save, and end-card rows

These are literal UI-page nodes. Process/menu controllers own focus and navigation; a nonzero next/alternate appears only where the two-choice `DialogueNode` contract is used. The three-item Title menu is composed from `TITLE_001..003` by `SCENE_TITLE` and therefore is not falsely encoded as a binary dialogue choice.

```c
DROW(UI_INTERACT,0x5420,21536,0x9420,37920,0,0,0,0,0,0x8600,0,0x08,0,ROOT_UI,"{A} INTERACT")
DROW(UI_EXAMINE,0x5421,21537,0x9421,37921,0,0,0,0,0,0x8600,0,0x08,0,ROOT_UI,"{A} EXAMINE")
DROW(UI_OPEN_RELAY,0x5422,21538,0x9422,37922,0,0,0,0,0,0x8600,0,0x08,0,ROOT_UI,"{C-DOWN} FIELD RELAY")
DROW(UI_PAUSED_DISCONNECT,0x5423,21539,0x9423,37923,0,0,0,0,0,0x8600,0,0x08,0,ROOT_UI,"CONTROLLER DISCONNECTED")
DROW(UI_RECONNECT,0x5424,21540,0x9424,37924,0,0,0,0,0,0x8600,0,0x08,0,ROOT_UI,"Reconnect a controller to continue.")
DROW(UI_SAVING,0x5425,21541,0x9425,37925,0,0,0,0,0,0x8600,0,0x08,0,ROOT_UI,"RECORDING RESONANCE...")
DROW(UI_SAVE_DONE,0x5426,21542,0x9426,37926,0,0,0,0,0,0x8600,0,0x18,60,ROOT_UI,"RESONANCE RECORDED")
DROW(UI_SAVE_FAILED,0x5427,21543,0x9427,37927,0,0x543B,0x543C,0,0,0x8600,0,0x02,0,ROOT_UI,"The record could not be written. Continue without saving?")
DROW(UI_LOADING_ANNEX,0x5428,21544,0x9428,37928,0,0,0,0,0,0x860E,0,0x08,0,ROOT_UI,"MERIDIAN RESEARCH ANNEX")
DROW(UI_LOADING_ESTATE,0x5429,21545,0x9429,37929,0,0,0,0,0,0x860E,0,0x08,0,ROOT_UI,"VEYRA OBSERVATORY ESTATE")

DROW(TITLE_001,0x542A,21546,0x942A,37930,0,0,0,0,0,0x8600,0,0x08,0,ROOT_UI,"NEW GAME")
DROW(TITLE_002,0x542B,21547,0x942B,37931,0,0,0,0,0,0x8600,0,0x08,0,ROOT_UI,"CONTINUE")
DROW(TITLE_003,0x542C,21548,0x942C,37932,0,0,0,0,0,0x8600,0,0x08,0,ROOT_UI,"OPTIONS")
DROW(TITLE_NEW_CONFIRM,0x542D,21549,0x942D,37933,0,0x5442,0x5443,0,0,0x8600,0,0x02,0,ROOT_UI,"Begin a new Resonance record?")
DROW(TITLE_OVERWRITE_CONFIRM,0x542E,21550,0x942E,37934,0,0x5444,0x5445,0,0,0x8600,0,0x02,0,ROOT_UI,"This will replace the current record.")
DROW(TITLE_INVALID_SAVE,0x542F,21551,0x942F,37935,0,0x5446,0x5447,0,0,0x8600,0,0x02,0,ROOT_UI,"This Resonance record cannot be read. Begin a new record?")
DROW(OPENING_INSERT_CUTSCENE,0x5430,21552,0x9430,37936,0,0,0,0,0,0x8600,0,0x08,0,ROOT_UI,"INSERT CUTSCENE HERE")
DROW(OPENING_SKIP_PROMPT,0x5431,21553,0x9431,37937,0,0,0,0,0,0x8600,0,0x08,0,ROOT_UI,"{A} / {START} SKIP")

DROW(NAME_001,0x5432,21554,0x9432,37938,0,0,0,0,0,0x8600,0,0x08,0,ROOT_UI,"FIELD CALLSIGN")
DROW(NAME_002,0x5433,21555,0x9433,37939,0,0,0,0,0,0x8600,0,0x08,0,ROOT_UI,"{A} ENTER   {B} DELETE   {START} CONFIRM")
DROW(NAME_EMPTY,0x5434,21556,0x9434,37940,0,0,0,0,0,0x8600,0,0x08,0,ROOT_UI,"Enter at least one letter.")
DROW(NAME_CONFIRM,0x5435,21557,0x9435,37941,0,0x5448,0x5449,0,0,0x8600,0,0x02,0,ROOT_UI,"Use {PLAYER}?")
DROW(NAME_CANCEL,0x5436,21558,0x9436,37942,0,0x544A,0x544B,0,0,0x8600,0,0x02,0,ROOT_UI,"Return to the title?")
DROW(UI_TRANSITION_BUSY,0x5437,21559,0x9437,37943,0,0,0,0,0,0x8600,0,0x08,0,ROOT_UI,"Finish the current transition first.")
DROW(UI_TRAVEL_FAILED,0x5438,21560,0x9438,37944,0,0,0,0,0,0x8600,0,0x08,0,ROOT_UI,"Travel could not be completed.")

DROW(END_GAME_MARK,0x5439,21561,0x9439,37945,0,0,0,0,0,0x8600,0,0x18,45,ROOT_UI,"N64GAME")
DROW(END_OPENING_CHAPTER,0x543A,21562,0x943A,37946,0,0,0,0,0,0x8600,0,0x08,60,ROOT_UI,"END OF OPENING CHAPTER")
DROW(END_RETRY_SAVE,0x543B,21563,0x943B,37947,0,0,0,0,0,0x8600,0,0x08,0,CHOICE_TARGET,"RETRY SAVE")
DROW(END_CONTINUE_UNSAVED,0x543C,21564,0x943C,37948,0,0,0,0,0,0x8600,0,0x08,0,CHOICE_TARGET,"CONTINUE UNSAVED")
DROW(END_CONTINUE_EXPLORING,0x543D,21565,0x943D,37949,0,0,0,0,0,0x8600,0,0x08,0,CHOICE_TARGET,"CONTINUE EXPLORING")
DROW(END_RETURN_TO_TITLE,0x543E,21566,0x943E,37950,0,0,0,0,0,0x8600,0,0x08,0,CHOICE_TARGET,"RETURN TO TITLE")
DROW(END_UNSAVED_WARNING,0x543F,21567,0x943F,37951,0,0x5440,0x5441,0,0,0x8600,0,0x02,0,ROOT_UI,"Unsaved opening progress will be lost. Return to title?")
DROW(END_STAY,0x5440,21568,0x9440,37952,0,0,0,0,0,0x8600,0,0x08,0,CHOICE_TARGET,"STAY")
DROW(END_RETURN,0x5441,21569,0x9441,37953,0,0,0,0,0,0x8600,0,0x08,0,CHOICE_TARGET,"RETURN")

DROW(TITLE_NEW_BEGIN,0x5442,21570,0x9442,37954,0,0,0,0,0,0x8600,0,0x08,0,CHOICE_TARGET,"BEGIN")
DROW(TITLE_NEW_BACK,0x5443,21571,0x9443,37955,0,0,0,0,0,0x8600,0,0x08,0,CHOICE_TARGET,"BACK")
DROW(TITLE_OVERWRITE_REPLACE,0x5444,21572,0x9444,37956,0,0,0,0,0,0x8600,0,0x08,0,CHOICE_TARGET,"REPLACE")
DROW(TITLE_OVERWRITE_BACK,0x5445,21573,0x9445,37957,0,0,0,0,0,0x8600,0,0x08,0,CHOICE_TARGET,"BACK")
DROW(TITLE_INVALID_NEW_GAME,0x5446,21574,0x9446,37958,0,0,0,0,0,0x8600,0,0x08,0,CHOICE_TARGET,"NEW GAME")
DROW(TITLE_INVALID_BACK,0x5447,21575,0x9447,37959,0,0,0,0,0,0x8600,0,0x08,0,CHOICE_TARGET,"BACK")
DROW(NAME_CONFIRM_YES,0x5448,21576,0x9448,37960,0,0,0,0,0,0x8600,0,0x08,0,CHOICE_TARGET,"YES")
DROW(NAME_CONFIRM_EDIT,0x5449,21577,0x9449,37961,0,0,0,0,0,0x8600,0,0x08,0,CHOICE_TARGET,"EDIT")
DROW(NAME_CANCEL_KEEP_EDITING,0x544A,21578,0x944A,37962,0,0,0,0,0,0x8600,0,0x08,0,CHOICE_TARGET,"KEEP EDITING")
DROW(NAME_CANCEL_RETURN,0x544B,21579,0x944B,37963,0,0,0,0,0,0x8600,0,0x08,0,CHOICE_TARGET,"RETURN")
DROW(OPTIONS_APPLY,0x544C,21580,0x944C,37964,0,0,0,0,0,0x8600,0,0x08,0,CHOICE_TARGET,"APPLY")
DROW(OPTIONS_CANCEL,0x544D,21581,0x944D,37965,0,0,0,0,0,0x8600,0,0x08,0,CHOICE_TARGET,"CANCEL")
DROW(MAP_TRAVEL_ACTION,0x544E,21582,0x944E,37966,0,0,0,0,0,0x860E,0,0x08,0,CHOICE_TARGET,"TRAVEL")
DROW(MAP_TRAVEL_BACK,0x544F,21583,0x944F,37967,0,0,0,0,0,0x860E,0,0x08,0,CHOICE_TARGET,"BACK")
DROW(MAP_RETURN_ACTION,0x5450,21584,0x9450,37968,0,0,0,0,0,0x860E,0,0x08,0,CHOICE_TARGET,"TRAVEL")
DROW(MAP_RETURN_BACK,0x5451,21585,0x9451,37969,0,0,0,0,0,0x860E,0,0x08,0,CHOICE_TARGET,"BACK")
DROW(END_MENU_ROOT,0x5452,21586,0x9452,37970,0,0x543D,0x543E,0,0,0x8600,0,0x02,0,ROOT_UI,"END OF OPENING CHAPTER")
```

## 3. Typed acquisition and root ownership

The following rows are generator inputs to the existing typed owner tables (`StoryStartEdgeDef`, `StoryTriggerBindingDef`, `NpcOccurrenceVariantDef`, encounter result flow, tutorial flow, and process UI bindings). Controllers may resolve rows by typed source key only; hard-coded `CharacterId`, `DialogueId`, or copy selection is forbidden. An accepted source edge is generation-bound, clears input latches, reserves DialogueController ownership, and discards one poll frame before the root can accept input.

### 3.1 Mandatory live and loaded-checkpoint starts

| Typed source | Root | Exact precondition and timing | Already-set, revisit, and failure behavior |
|---|---|---|---|
| `TUTORIAL_INTRO_COMPLETE / TUTORIAL_SCRIPT_OPENING` | `SIM_001` | `STORY_PRECOND_SIM_TUTORIAL_READY`; the first request reached `COMMITTED`, possibly after immutable Retry; coherent sim spawn; all four actors/nameplates already staged; authored 180–240-tick fly-in complete; before gameplay input | Return-to-Title abort terminates the branch and emits no tutorial-start edge; otherwise exact-once per runtime generation and stale intro completion is ignored |
| `CONTINUE_LOADED_STABLE / CHECKPOINT_AFTER_NAME` | `SIM_001` | same precondition; loader constructs a fresh dormant tutorial owner, stages all four actors, runs the same 180–240-tick fly-in, then acquires the root before input | reboot-reachable; never resumes a serialized partial tutorial; no double construction |
| `TRANSITION_COMMIT / TRANS_DEF_SIM_REVEAL` | `ANNEX_INTRO_001` | `STORY_PRECOND_ANNEX_INTRO_READY`; before free control | duplicate generation ignored; completed onboarding fails precondition |
| `INTERACTION_ACCEPT / INT_NPC_OREN` | `OREN_001` | `STORY_PRECOND_OREN_ASSIGNMENT_READY`; priority over the prechapter repeat row, while mutually exclusive post-chapter rows use priorities 5/6 | if quest already started, this row is false and cannot replay `OREN_003` action; post-chapter rows cannot become true before slice completion |
| `INTERACTION_ACCEPT / INT_NPC_JO` | `JO_RELAY_001` | `STORY_PRECOND_JO_RELAY_READY`; priority 3 | false before assignment and after Relay unlock; cancel before acquisition changes nothing |
| `INTERACTION_ACCEPT / INT_NPC_PELL` | `PELL_TRACE_001` | `STORY_PRECOND_PELL_TRACE_READY`; priority 3 | false before Relay checkpoint and after Tavi report; Pell chain alone includes Sera Relay pages |
| `WORLD_VOLUME_ENTER / INT_RUSK_CONFRONTATION_VOLUME` | `RUSK_PRE_001` | `STORY_PRECOND_RUSK_FIRST_CONFRONTATION`; two stable overlap ticks; resources coherent | exact-once generation; backing out of volume before acquisition changes nothing |
| `TRANSITION_COMMIT / TRANS_DEF_MAP_RESELECT_ESTATE` | `RUSK_RETRY_001` | `STORY_PRECOND_RUSK_LATER_CONFRONTATION`; before control | captures a new pre-Rusk snapshot only on dismissal; cannot use stale defeat snapshot |
| `BATTLE_DEFEAT_FLOW_COMMIT / TRANS_DEF_RUSK_BATTLE_RETRY` | `RUSK_RETRY_IMMEDIATE_001` | current reissued defeat token and restored snapshot; battle spawn coherent | rollback rebuilds defeat menu; dismissal starts already-restored encounter once |
| `ENCOUNTER_VICTORY_COMMIT / ENCOUNTER_RUSK_COURTYARD` | `RUSK_WIN_UI_001` | exact current result token; victory transaction accepted once | result chain owns UI then post-battle dialogue; reward cannot be accepted twice |
| `ENCOUNTER_DEFEAT_COMMIT / ENCOUNTER_RUSK_COURTYARD` | `RUSK_LOSE_001` | exact current result token and live pre-Rusk snapshot | choice target acceptance, not result text, owns Retry/Return continuation |
| `TRANSITION_COMMIT / TRANS_DEF_COURTYARD_TO_FOYER` | `RUSK_ENTRY_001` | `STORY_PRECOND_RUSK_FOYER_ENTRY_READY`; before control; conversation-once row `{root=RUSK_ENTRY_001,terminal=RUSK_ENTRY_003,bit=8}` clear | terminal close sets bit 8; interruption before terminal leaves clear; set bit hides the whole chain |
| `TRANSITION_COMMIT / TRANS_DEF_HALL_TO_STUDY` | `REUNION_001` | `STORY_PRECOND_REUNION_STUDY_READY`; before control | ENTER trigger commits Tavi found before first text; resource failure prevents acquisition |
| `WORLD_VOLUME_ENTER / INT_ANNEX_RETURN_RESOLUTION_VOLUME` | `RETURN_001` | `STORY_PRECOND_RETURN_ATRIUM_READY`; player and derived Tavi follower overlap for 2 stable ticks after 600–1350 normal-walk ticks of player-controlled threshold-to-atrium traversal | portal/transition commit never starts Return; follower recovery outside volume waits; one debounced acquisition |
| `MILESTONE_SAVE_RESOLVED / MILESTONE_TAVI_RETURNED` | `STORY_SEQUENCE_OPENING_HOOK -> HOOK_001` | `STORY_PRECOND_HOOK_READY`; only after the reserved `RETURN_007` owner is closed and its exact mandatory save reaches terminal `COMMITTED` or explicitly accepted `CONTINUED_DIRTY` | Retry/failure UI retains ownership and emits no start; the terminal token releases that owner before the live Hook starts, so its final save cannot overlap the Tavi checkpoint request |
| `CONTINUE_LOADED_STABLE / CHECKPOINT_TAVI_RETURNED` | `STORY_SEQUENCE_OPENING_HOOK -> HOOK_001` | same precondition; slice incomplete; stable Annex resources | mandatory reboot recovery; restarts at `HOOK_001`, never at a mid-hook node |
| `STABLE_POST_REVEAL / TRANS_DEF_RUSK_RETURN_ANNEX` | `SERA_RUSK_RETURN_001` | `STORY_PRECOND_RUSK_RETURN_LINE_READY`; Return checkpoint already committed; dialogue once bit 0 clear | first stable threshold control only; retention behavior in §6 |
| `CONTINUE_LOADED_STABLE / CHECKPOINT_RUSK_RETURN_TO_ANNEX` | `SERA_RUSK_RETURN_001` | same precondition and clear bit 0; first stable threshold control after load | reboot recovery is distinct from live transition start; set bit suppresses it |

`SIM_002` dismissal owns `ACTION_SIM_TUTORIAL_START (0x4162)`, which compares the already-live tutorial owner in `INTRO_DIALOGUE` and publishes `GATE_1`. It allocates no actor, encounter, UI, or battle heap. This single owner works for both SIM roots above because each load/live path creates one fresh generation.

### 3.2 Tutorial-owned roots

| Tutorial owner event | Root | Completion/repeat |
|---|---|---|
| `GATE1_INSTRUCTION_REQUIRED` | `SIM_G1_HP` | chain closes at `SIM_G1_INFO` |
| `GATE1_UNMET` | `SIM_G1_REPEAT` | no state or enemy escalation; next safe command boundary only |
| `GATE1_ACCEPTED` | `SIM_G1_DONE` | then phase advances to gate 2 |
| `GATE2_INSTRUCTION_REQUIRED` | `SIM_G2_001` | chain closes at `SIM_G2_002`; UI overlays may independently acquire `SIM_EFFECT_STRONG/RESIST` |
| `GATE2_UNMET` | `SIM_G2_REPEAT` | no state or enemy escalation |
| `GATE2_ACCEPTED` | `0` | typed immediate phase edge to gate 3; no filler dialogue root |
| `GATE3_INSTRUCTION_REQUIRED` | `SIM_G3_001` | chain closes at `SIM_G3_002` |
| `GATE3_UNMET` | `SIM_G3_REPEAT` | next safe command boundary only |
| `GATE3_ACCEPTED` | `0` | typed immediate phase edge to gate 4; no filler dialogue root |
| `GATE4_INSTRUCTION_REQUIRED` | `SIM_G4_001` | chain closes at `SIM_G4_002` |
| `GATE4_UNMET` | `SIM_G4_REPEAT` | no calibration before honest meter ≥70 |
| `GATE4_FULL` | `SIM_G4_FULL` | exactly once after meter reaches 100 |
| `GATE5_INSTRUCTION_REQUIRED` | `SIM_G5_001` | `SIM_FINISHER_INFO` is a separate move-info overlay |
| `GATE5_UNMET` | `SIM_G5_REPEAT` | meter stays full; safe round boundary |
| `GATE5_FINISHER_RESOLVED` | `SIM_G5_DONE` | chain reaches `SIM_RESULT_COMPLETE`; encounter result acceptance owns dissolve |
| `TUTORIAL_IMPOSSIBLE_STATE` | `SIM_RESULT_INTERRUPTED` | confirm advances to `SIM_RESULT_RESTART`; restart destroys/rebuilds tutorial-local state only |
| `PRE_GATE5_EARLY_KO_CLAMP` | `SIM_RESULT_CALIBRATION_HOLD` | auto-closes after 45 presentation ticks; no input/state action |

Every tutorial event carries `(runtime_generation,tutorial_generation,battle_generation,event_epoch,encounter_id,phase,event_id)` in the exact `TutorialEventToken`. `TutorialEventRouteDef` is set-equal with all seventeen rows above; the two zero-root Accepted rows are immediate typed phase edges. A repeated/stale event is ignored. Only one tutorial/root acquisition may be pending, and story/result dialogue preempts tutorial callouts. `SIM_RESULT_RESTART` dismissal owns `ACTION_SIM_TUTORIAL_RESTART`; it is the sole path that reconstructs the interrupted runtime.

### 3.3 Interaction variants, optional era copy, and post chapter

Variant selection occurs before saved-once lookup. Prior optional-talk history can suppress an animation, but can never select PRE versus POST copy.

| Interaction/occurrence | Priority | Exact condition | Root | Once/revisit behavior |
|---|---:|---|---|---|
| `NPC_OCCURRENCE_ANNEX_MARA` | 2 | `COND_NPC_MARA_POST`: Find-Tavi objective active or any later chapter state | `MARA_POST_001` | occurrence bit 0 controls first-presentation animation only |
| same | 1 | `COND_NPC_MARA_PRE`: exact complement in legal pre-Find range | `MARA_PRE_001` | first-ever late talk still selects POST |
| `INT_NPC_JO` | 3 | `STORY_PRECOND_JO_RELAY_READY` | `JO_RELAY_001` | mandatory acquisition; no NPC once mutation until chain closes |
| `NPC_OCCURRENCE_ANNEX_JO` | 2 | `COND_NPC_JO_POST`: Relay unlocked | `JO_POST_001` | occurrence bit 1 affects animation only |
| same | 1 | `COND_NPC_JO_PRE`: Relay not unlocked and mandatory-ready row false | `JO_PRE_001` | PRE remains PRE across repeats until state changes |
| `INT_NPC_PELL` | 3 | `STORY_PRECOND_PELL_TRACE_READY` | `PELL_TRACE_001` | mandatory chain priority |
| `NPC_OCCURRENCE_ANNEX_PELL` | 2 | `COND_NPC_PELL_POST`: Estate destination unlocked | `PELL_POST_001` | occurrence bit 2 affects animation only |
| same | 1 | `COND_NPC_PELL_PRE`: exact complement and mandatory-ready false | `PELL_PRE_001` | no pre/post inference from the bit |
| `INT_NPC_OREN` | 2 | Relay quest started and Relay not yet unlocked | `OREN_004` | safe pre-retrieval repeat chain `004->005->006`; action-bearing `OREN_003` is bypassed; later pre-chapter eras intentionally offer no Oren dialogue |
| `INT_NPC_TAVI_FOLLOW (0x201E)` | 3 | derived follower active and stable | `TAVI_FOLLOW_001` | repeatable; no save or story action |
| `INT_NPC_SERA_POST (0x201F)` | 3 | slice complete, post-chapter exploration | `POST_SERA_001` | repeatable |
| `INT_NPC_OREN` | 5 | slice complete and durable final outcome `SAVED` (runtime may be clean or newer-dirty) | `POST_OREN_001` | outranks assignment/repeat rows; secure opening record remains truthful |
| `INT_NPC_OREN` | 6 | slice complete and final outcome `CONTINUE_UNSAVED`/dirty | `POST_OREN_UNSAVED_001` | remains selected until successful write or dirty runtime discard |
| `INT_NPC_TAVI_POST (0x2020)` | 3 | slice complete | `POST_TAVI_001` | repeatable |
| `INT_NPC_PELL` | 5 | slice complete | `POST_PELL_001` | outranks `PELL_POST_001` |
| `INT_NPC_RUSK_POST (0x2021)` | 3 | slice complete, Estate accessible, Rusk won | `POST_RUSK_001` | repeatable |
| `INT_NPC_IVO_POST (0x2022)` | 3 | slice complete, Estate study accessible | `POST_IVO_001` | repeatable |

For every shared interaction, generator truth-table enumeration over legal chapter states must prove exactly one highest-priority row or an intentional no-dialogue state. Equal-priority simultaneous rows, missing mandatory rows, or once-bit-dependent era copy fail generation.

### 3.4 Annex and Estate skimmer acquisition

| Owner | Exact selector | Root/continuation | Cancel, repeat, and persistence |
|---|---|---|---|
| `INT_SKIMMER_MAP` | `field_relay_unlocked=false` | `EXIT_LOCKED_NO_RELAY` | close returns stable threshold control; no mutation |
| `INT_SKIMMER_MAP` | Relay true, Estate destination false | `EXIT_LOCKED_NO_TRACE` | close returns control; no mutation |
| `INT_SKIMMER_MAP` | Relay+Estate true, follower inactive, `annex_exit_cleared=false` | `EXIT_READY_001` | STAY changes nothing; OPEN target ENTER owns `ACTION_EXIT_OPEN_FIRST_SERA (0x4163)` and starts `SERA_DEPART_001` after reserved close |
| `SERA_DEPART_001` dismissal | clear once bit 7 and first-departure condition | `ACTION_SERA_DEPART_CONTINUE_MAP (0x4167)` -> `TRANS_DEF_THRESHOLD_TO_MAP` | transition recipe atomically publishes bit 7 with departure flag/checkpoint; pre-publish failure leaves both clear and line replayable |
| `INT_SKIMMER_MAP` | Relay+Estate true, follower inactive, `annex_exit_cleared=true` | `EXIT_READY_REPEAT_001` | STAY no-op; OPEN target owns `ACTION_EXIT_OPEN_REPEAT_MAP (0x4164)` and never replays Sera |
| `INT_ESTATE_SKIMMER` | derived follower active, dialogue bit 9 clear, player chooses Return/Travel | `RUSK_EXIT_001 -> TAVI_EXIT_001` | Back before acquisition changes nothing; terminal dismissal stages bit 9 and requests `TRANS_DEF_STUDY_RETURN_TO_MAP` through `0x4165` |
| `INT_ESTATE_SKIMMER` | derived follower active, bit 9 set | `RETURN_SKIMMER_REPEAT_001` | no Rusk/Tavi replay; dismissal retries same transition through `0x4166` |
| `INT_ESTATE_SKIMMER` | follower inactive | normal Estate map-exit UI, no story root | cannot acquire return chain |

The Rusk/Tavi terminal continuation reserves stable-source save/transition and follower-handoff capacity before publishing bit 9. Failure before publish leaves the bit clear. If the player explicitly continues a dirty in-memory departure after an honest write failure, same-session re-entry routes to the repeat root; power loss loads the last verified checkpoint and may replay only if the terminal exchange was never durably written.

### 3.5 World-map route table

| Focus/follower/story state | Prompt | Confirm target -> exact transition | Back behavior |
|---|---|---|---|
| `MAP_SELECTION_ESTATE`, follower inactive, `estate_arrived=false` | `MAP_TRAVEL_CONFIRM` | `MAP_TRAVEL_ACTION -> TRANS_DEF_MAP_TO_ESTATE` | `MAP_TRAVEL_BACK`; close, clear selection edge, no progress |
| `MAP_SELECTION_ESTATE`, follower inactive, `estate_arrived=true` | `MAP_TRAVEL_CONFIRM` | `MAP_TRAVEL_ACTION -> TRANS_DEF_MAP_RESELECT_ESTATE` | same no-progress Back |
| `MAP_SELECTION_ANNEX`, follower inactive | `MAP_RETURN_CONFIRM` | `MAP_RETURN_ACTION -> TRANS_DEF_MAP_TO_THRESHOLD` | `MAP_RETURN_BACK`; no progress |
| `MAP_SELECTION_ANNEX`, follower active | `MAP_RETURN_CONFIRM` | `MAP_RETURN_ACTION -> TRANS_DEF_MAP_RETURN_TO_ANNEX` | no-progress Back; follower remains valid |
| `MAP_SELECTION_ESTATE`, follower active | `MAP_TRAVEL_CONFIRM` | `MAP_TRAVEL_ACTION -> TRANS_DEF_MAP_RETURN_RESELECT_ESTATE` | no-progress Back; follower remains valid |
| `MAP_SELECTION_BACK` | no prompt | exact generation-current `MapCancelRouteDef` transition | return to the physical source threshold/courtyard with progress unchanged; follower handoff follows captured origin |

The map controller selects one row from an immutable generation-bound selection snapshot, reserves the exact transition slot before consuming confirm, and clears A/B latches on prompt open/close. A prompt cannot select a route by reading copy IDs, and a failed load returns to the same map selection without story mutation. Prompt BACK only closes that prompt. Map-level Back with no prompt resolves the captured Annex/inactive, Estate/inactive, or Estate/follower origin and submits its exact SAVE_NONE return transition; a stale or impossible origin cannot fall through to controller code.

## 4. First-use HelpPrompt registry

This section is an exact projection of the canonical `HelpPromptDef` table. Completion masks use OR semantics. All rows carry exact flags `0x7F`: `NON_STACKING + REQUIRE_STABLE_CONTROL + DEFER_DURING_DIALOGUE + DEFER_DURING_TRANSITION + PAUSE_ON_CONTROLLER_LOSS + PERSIST_ON_NEXT_LEGAL_SAVE + DO_NOT_SEIZE_MOVEMENT`. Reserved is zero.

```c
static const HelpPromptDef OPENING_HELP_PROMPTS[6] = {
    { HELP_MOVE,   STR_HELP_MOVE,
      SCENE_ANNEX_INTERIOR, ZONE_ANNEX_ATRIUM,
      0x0000000F, 90, HELP_TRIGGER_FIRST_STABLE_ATRIUM_CONTROL,
      1, 0xFF, 60, 0x7F, 0 },
    { HELP_CAMERA, STR_HELP_CAMERA,
      SCENE_ANNEX_INTERIOR, ZONE_ANNEX_ATRIUM,
      0x00000030, 0, HELP_TRIGGER_FIRST_STABLE_ATRIUM_CONTROL,
      2, 1, 59, 0x7F, 0 },
    { HELP_PAUSE,  STR_HELP_PAUSE,
      SCENE_ANNEX_INTERIOR, ZONE_ANNEX_ATRIUM,
      0x00000040, 0, HELP_TRIGGER_FIRST_STABLE_ATRIUM_CONTROL,
      3, 2, 58, 0x7F, 0 },
    { HELP_PARTY,  STR_HELP_PARTY,
      SCENE_ANNEX_INTERIOR, 0,
      0x00000280, 0, HELP_TRIGGER_FIELD_RELAY_UNLOCKED_STABLE,
      4, 0xFF, 50, 0x7F, 0 },
    { HELP_SAVE,   STR_HELP_SAVE,
      SCENE_ANNEX_INTERIOR, 0,
      0x00000300, 0, HELP_TRIGGER_FIELD_RELAY_UNLOCKED_STABLE,
      5, 4, 49, 0x7F, 0 },
    { HELP_MAP,    STR_HELP_MAP,
      SCENE_WORLD_MAP, ZONE_WORLD_MAP_DESERT,
      0x00000400, 1, HELP_TRIGGER_FIRST_WORLD_MAP_CONTROL,
      6, 0xFF, 70, 0x7F, 0 }
};
```

| Help | Exact completion OR-mask | Canonical behavior |
|---|---|---|
| `HELP_MOVE` | `TIMER_90_TICKS + MOVE_DEMONSTRATED + RUN_DEMONSTRATED + INTERACT_DEMONSTRATED` | appears at first stable Atrium control; any demonstrated action completes it immediately, otherwise its timer event completes only after 90 actually visible 30 Hz gameplay ticks, exactly 3 seconds |
| `HELP_CAMERA` | `CAMERA_ADJUSTED + EXPLICIT_DISMISS` | predecessor bit 1 must be set; one typed camera-adjust event or explicit-dismiss event completes it; no angle threshold is invented here |
| `HELP_PAUSE` | `PAUSE_OPENED` | predecessor bit 2 must be set; only successful Pause ownership acquisition emits completion |
| `HELP_PARTY` | `PARTY_SCREEN_OPENED + EXTERIOR_EXIT_PROMPT_OPENED` | Relay-unlocked stable trigger; either opening PARTY or reaching the exterior exit prompt completes it |
| `HELP_SAVE` | `MANUAL_SAVE_COMMITTED + EXTERIOR_EXIT_PROMPT_OPENED` | predecessor bit 4 must be set; only a verified manual-save commit or the exterior exit fallback completes it |
| `HELP_MAP` | `WORLD_MAP_CONTROL_ACQUIRED` | priority 70; first world-map control trigger; minimum one visible tick guarantees the prompt renders for one frame before the acquisition event completes it |

One `HelpPromptOwner` holds a nonzero runtime generation and at most one active row. Eligible rows sort by priority descending, then DialogueId: Map `70`, Move `60`, Camera `59`, Pause `58`, Party `50`, Save `49`. A row cannot acquire while dialogue, cutscene, transition, battle, menu, or another help owns presentation. Stable-control triggers debounce for one complete poll/render frame. Because movement is not seized, Move/Run/Interact/Camera demonstrations can occur while their prompt is visible.

Each completion event carries runtime and producing-subsystem generations and is accepted once. Completion begins a scratch one-shot transaction, resolves the exact help DialogueOnceRegistry row and predecessor, sets only its bit, publishes once, then closes presentation. `INT_SKIMMER_MAP` emits `EXTERIOR_EXIT_PROMPT_OPENED` immediately before first/repeat exit selection; it may complete Party and Save but never Move, Camera, or Pause.

Controller loss freezes visible ticks, clears event/input latches, retains the active prompt, and cannot set a bit. Reconnect discards one full poll frame before events resume. A deferred prompt carries no stale input edge and reacquires only at stable control. Help never requests or coalesces a write: its bit persists on the next otherwise-legal checkpoint/manual/transition save, and reboot reoffers only prompts whose bit was not durably written. Unknown event/flag bits, mask/tick/trigger/location mismatch, duplicate once bit or priority, unmet predecessor, non-help registry owner, or nonzero reserved fails generation.

## 5. Process and UI page ownership

| Typed UI owner | Literal page IDs | Binding rule |
|---|---|---|
| `SCENE_TITLE / TITLE_MENU` | `TITLE_001`, `TITLE_002`, `TITLE_003` | fixed three-item order; Continue disabled by verified-save state without changing copy |
| `TITLE_NEW_GAME_PROMPT` | `TITLE_NEW_CONFIRM -> TITLE_NEW_BEGIN/TITLE_NEW_BACK` | BEGIN emits `PROCESS_ACCEPT_NEW_GAME`; BACK closes, no draft |
| `TITLE_OVERWRITE_PROMPT` | `TITLE_OVERWRITE_CONFIRM -> TITLE_OVERWRITE_REPLACE/TITLE_OVERWRITE_BACK` | REPLACE creates only an in-memory draft; old page is not erased here |
| `TITLE_INVALID_SAVE_PROMPT` | `TITLE_INVALID_SAVE -> TITLE_INVALID_NEW_GAME/TITLE_INVALID_BACK` | invalid raw pages remain untouched; Back returns title |
| `SCENE_OPENING_SLOT` | `OPENING_INSERT_CUTSCENE` + `OPENING_SKIP_PROMPT` | two co-rendered layers for exactly 106 presentation ticks; A/Start calls the one idempotent finalizer and never enters DialogueController sequencing |
| `SCENE_NAME_ENTRY` | `NAME_001`, `NAME_002` | persistent header/help surfaces; grid data is separate typed UI data |
| `NAME_VALIDATION_EMPTY` | `NAME_EMPTY` | A returns grid; no draft commit |
| `NAME_CONFIRM_PROMPT` | `NAME_CONFIRM -> NAME_CONFIRM_YES/NAME_CONFIRM_EDIT` | YES emits one name-confirm accept token; EDIT restores cursor/draft |
| `NAME_CANCEL_PROMPT` | `NAME_CANCEL -> NAME_CANCEL_KEEP_EDITING/NAME_CANCEL_RETURN` | Return discards only uninitialized draft; B never opens this prompt |
| `OPTIONS_FOOTER` | typed `SETTINGS_EDITOR` view + `OPTIONS_APPLY`, `OPTIONS_CANCEL` | nine exact controls plus Reset/Apply/Cancel; Title Apply is profile-only, Pause Apply reserves the Settings save route; neither button is a dialogue StoryAction owner |
| `PAUSE_MENU` | process-static Resume / Party / Field Relay / Settings / Return to Title | fixed five-item order; Party/Field Relay require no battle owner; Settings requires no battle owner except the exact Sim-Intro tutorial safe boundary; real battle enables only Resume/Return; owner captures/restores the physical gameplay origin |
| `FIELD_RELAY / RELAY_PARTY` | Party tab + typed Party runtime view + Back | legal before Relay only when opened from Pause; other tabs disabled; Back restores captured origin |
| `FIELD_RELAY / RELAY_MESSAGES` | five tabs + typed Messages runtime view + Back | graph copy is display-only; opening/reading sets no once/story bit |
| `FIELD_RELAY / RELAY_RESONANCE` | five tabs + typed Resonance runtime view + Back | information-only Sync/Team Link/record view |
| `FIELD_RELAY / RELAY_MAP` | five tabs + typed Map runtime view + Back | information-only; cannot submit a TransitionId |
| `FIELD_RELAY / RELAY_SAVE` | five tabs + typed Save runtime view + Record + Back | only Record may open the typed manual-save confirm and producer |
| `MANUAL_SAVE_CONFIRM` | process-static confirm / Record / Back | modal closes before Manual Relay capture; Back returns only to Relay Save with no mutation |
| `INTERACTION_PROMPT_RENDERER` | `UI_INTERACT`, `UI_EXAMINE`, `UI_OPEN_RELAY` | prompt strings are selected by typed interaction/page capability only |
| `CONTROLLER_OWNER` | `UI_PAUSED_DISCONNECT`, `UI_RECONNECT` | freezes fixed logic and typewriter; reconnect clears edges before resuming exact owner |
| `SAVE_SERVICE` | `UI_SAVING`, `UI_SAVE_DONE` | DONE only after verified write; nonfinal failures remain process-static under their exact typed policy and never acquire a Dialogue root |
| `TRANSITION_LOADING_CARD` | `UI_LOADING_ANNEX`, `UI_LOADING_ESTATE` | shown only while real destination work/minimum authored travel runs; no fake wait |
| `TRANSITION_FAILURE` | `UI_TRANSITION_BUSY`, `UI_TRAVEL_FAILED` | fully revealed modal; dismissal returns the rollback owner |
| `WORLD_MAP` | `MAP_*`, `MAP_TRAVEL_*`, `MAP_RETURN_*` | exact route table in §3.5; labels do not dispatch by StringId |
| `SCENE_END_CHAPTER` | `END_GAME_MARK -> END_OPENING_CHAPTER` | authored mark/subtitle treatment only after the immutable final save outcome resolves; forbidden while the outcome is `PENDING` |
| `FINAL_SAVE_FAILURE` | `UI_SAVE_FAILED -> END_RETRY_SAVE/END_CONTINUE_UNSAVED` | Retry reuses immutable slice snapshot; Continue explicitly marks dirty |
| `END_CARD_MENU` | `END_MENU_ROOT -> END_CONTINUE_EXPLORING/END_RETURN_TO_TITLE` | available only after save outcome resolved |
| `END_DIRTY_RETURN_WARNING` | `END_UNSAVED_WARNING -> END_STAY/END_RETURN` | first Return only captures GAMEPLAY Pause or END_CARD origin; STAY restores its exact owner/state/focus; confirmed Return consumes that origin's fresh warning token/acknowledgement |
| `ROLLBACK_DIRTY_RETURN_WARNING` | `END_UNSAVED_WARNING -> END_STAY/END_RETURN` | distinct ROLLBACK_FATAL origin and acknowledgement; cannot consume gameplay/end-card warning state |

Every process binding is keyed by `(scene_id,ui_owner_id,state_variant)` and resolves DialogueIds, process-static strings, and typed runtime views through generated data. Process code may compare typed enum states but may not embed a DialogueId, StringId, literal copy, Relay field, Settings rule, or save-display formatter. The first Return press is a selector rather than an acknowledgement for all three dirty origins; only confirmed Return emits the exact origin-specific single-use ack plus current warning token. A battle-origin Return token is live only while the retained Pause snapshot still matches the current `BattleRuntimeOwner` runtime/battle generations and command/target safe phase. The existing clean/dirty stable-gameplay navigation rows then destroy that battle owner and campaign without reading Relay views, copying `BattleActor` HP, or serializing partial battle state; warning Stay restores the frozen boundary instead.

## 6. One-shot, action, save, and post-battle invariants

### 6.1 Dialogue and conversation once rows

| Bit | Registry owner | Root/terminal | Already-set behavior | Durable capture |
|---:|---|---|---|---|
| 0 | `SERA_RUSK_RETURN_001` | same/same | hide | exact retention replacement write below |
| 1 | `HELP_MOVE` | same/same | hide | next eligible save |
| 2 | `HELP_CAMERA` | same/same | hide | next eligible save |
| 3 | `HELP_PAUSE` | same/same | hide | next eligible save |
| 4 | `HELP_PARTY` | same/same | hide | next eligible save |
| 5 | `HELP_SAVE` | same/same | hide | next eligible save |
| 6 | `HELP_MAP` | same/same | hide | next eligible save |
| 7 | `SERA_DEPART_001` | same/same | hide | atomically in `TRANS_RECIPE_ANNEX_DEPARTURE` |
| 8 | `RUSK_ENTRY_003` | `RUSK_ENTRY_001/RUSK_ENTRY_003` conversation row | hide whole root | next stable transition/manual save |
| 9 | `TAVI_EXIT_001` | `RUSK_EXIT_001/TAVI_EXIT_001` | route skimmer to `RETURN_SKIMMER_REPEAT_001` | stable-source return save/transition continuation |

Bits 7 and 9 are staged with their required external continuation; failure before joint publish sets neither. Rusk entry sets bit 8 only on terminal close, never when page 1 advances. Examine bits `0..19` and NPC bits `0..2` remain the exact `DATA_SCHEMAS.md` registries; they are separate 64-bit sets and never alias dialogue bits.

### 6.2 Sera Return retention

`SERA_RUSK_RETURN_001` dismissal mirrors `ACTION_SERA_RUSK_RETURN_ONCE_SAVE (0x4161)`, whose sole action is `ACTION_REQUEST_RETENTION_SAVE / RETENTION_SAVE_SERA_RUSK_RETURN_ONCE`. Before consuming the line or bit 0, StoryTrigger reserves the owner close, save request slot, and immutable replacement-page buffer. It validates exact `CHECKPOINT_RUSK_RETURN_TO_ANNEX`, chapter 5, threshold current/last-safe locations, `BATTLE_RESULT_RETURN_TO_ANNEX`, and `ENCOUNTER_RUSK_COURTYARD`; it then merges bit 0 into prospective scratch, encodes that same-checkpoint snapshot, publishes the bit/owner close no-fail, and enqueues the write. This is not a milestone, does not promote chapter/checkpoint, and changes no location or battle fact.

Reservation/validation failure leaves the fully revealed line active and bit clear. Write failure leaves the coherent runtime dirty and shows Retry or explicit Continue Dirty; only a verified write guarantees power-loss suppression, so Continue Dirty must state the reboot replay risk honestly. Return to Title from dirty state uses the normal loss warning. A duplicate current-generation completion is a no-op.

### 6.3 Rusk victory presentation and restore timing

Victory commit applies Sync/Team Link/reward flags but preserves exact post-battle HP; `REWARD_RESTORE_HP` is clear. The result/post chain keeps gameplay control locked. Only `RUSK_POST_005` dismissal mirrors `ACTION_RUSK_POST_HEAL_AND_DOOR_BEGIN (0x4168)`: it atomically restores both real starters to derived max HP, then emits the generation-bound door-animation callback. The callback completion alone sets `FLAG_ESTATE_DOOR_OPEN` and requests `CHECKPOINT_RUSK_VICTORY`. Thus the visible promise, restore animation, logical HP mutation, door opening, and full-HP checkpoint occur in that order exactly once.

### 6.4 Node action mirrors

The only nonzero action mirrors in the 223 rows are: `ANNEX_INTRO_004=0x4151`, `ANNEX_INTRO_005=0x4152`, `OREN_003=0x4110`, `JO_RELAY_006=0x4140`, `SERA_RELAY_002=0x4141`, `PELL_TRACE_004=0x4142`, `RUSK_PRE_005=0x4111`, `RUSK_RETRY_001=0x4112`, `RUSK_RETRY_IMMEDIATE_001=0x4113`, `SERA_RUSK_RETURN_001=0x4161`, `RUSK_POST_005=0x4168`, `REUNION_001=0x4158`, `REUNION_004=0x4159`, `REUNION_011=0x415A`, `RETURN_005=0x415B`, `RETURN_007=0x415C`, `HOOK_005=0x415E`, `HOOK_010=0x415F`, `HOOK_014=0x4160`, `SIM_002=0x4162`, `SIM_RESULT_RESTART=0x4169`, `EXIT_READY_OPEN=0x4163`, `EXIT_READY_REPEAT_OPEN=0x4164`, `SERA_DEPART_001=0x4167`, `TAVI_EXIT_001=0x4165`, and `RETURN_SKIMMER_REPEAT_001=0x4166`. All other node action mirrors are literal zero. `RUSK_POST_005` starts its callback through `0x4168`; it does not directly own the callback outside StoryTrigger.

## 7. Generator validation and certification rules

Generation fails unless all of these checks pass:

1. Parse exactly 223 `DROW` records with 16 fields each. DialogueId, StringId, and symbol are independently unique. Every hex/decimal mirror agrees. The 16 bridge StringIds are exactly `0x6F01..0x6F10`; every other StringId equals its row's DialogueId plus `0x4000`.
2. Every nonzero next/alternate resolves. A choice has two nonzero targets. A non-choice has alternate zero. A terminal non-choice has `CLOSE_AFTER`. No chain has a cycle or exceeds 48 advances; the longest authored chain is the 14-page Hook.
3. Speaker is `0..9`, emote `0..11`, flags use only `0x1F`, camera is one of the 15 declared cues, and ticks are nonnegative. Auto time begins only after final-page reveal and pauses on controller loss.
4. All 160 first-column copy IDs in Story sections 5–6 resolve once and byte-match their exact UTF-8 source. Derived choice/repeat/process rows are additional and must retain their literal copy here. No Story copy is synthesized from speaker names or action prose.
5. All numeric DialogueId declarations in Data resolve to a row with the same value. Tutorial generic constants are aliases only to the canonical gate symbols. All 16 `MANDATORY_BRIDGE_DIALOGUE_NODES` fields and strings byte-match Data.
6. Every nonzero action xref equals exactly one compatible `StoryTriggerBindingDef`; DialogueController never calls it. Every mandatory root has one typed acquisition path in §3, including live and reboot paths. Selector conditions sharing an interaction are exhaustive/disjoint or explicitly allow no dialogue.
7. A one-shot flag resolves a live registry row. Conversation bit 8 resolves root and terminal. Optional PRE/POST is selected before once state. No ID modulo/truncation is used as a bit index.
8. `OPENING_HELP_PROMPTS` byte-compares with the six canonical `HelpPromptDef` rows: completion masks `0x0000000F/0x00000030/0x00000040/0x00000280/0x00000300/0x00000400`, visible ticks `90/0/0/0/0/1`, once bits `1..6`, predecessors `0xFF/1/2/0xFF/4/0xFF`, priorities `60/59/58/50/49/70`, flags `0x7F`, and reserved zero. Completion is OR, Move demonstrations may beat its 90-tick timer, Map renders one tick, and controller loss/defer cannot set a bit or carry an edge.
9. `SIM_002` advances an already-live tutorial; it never allocates the intro encounter. Return starts only from the atrium volume with both actors. Sera first departure, Rusk/Tavi exit, and Sera Return retention reserve their external continuation before publishing their once mutation.
10. Text packing proves at most four pages of three lines after an eight-character `{PLAYER}` substitution and fits the 320×240 safe rectangle. All supported glyphs, including `—`, `–`, `×`, and curly apostrophes, must exist in the font atlas or conversion fails.
11. Fuzz/golden tests cover every root, every next edge, both sides of every choice, every cancel/back path, all tutorial repeats, all six save-failure policies, controller loss on every page class, all once-set revisits, both loaded-checkpoint recovery starts, all Help completion alternatives, the Party/Save exterior fallback, Move at visible ticks 89/90, and Map before/after its first rendered tick.

Required automated command:

```sh
scripts/validate-dialogue-graph
```

Its success contract is: `223 nodes`, `160 story rows`, and `16 byte-exact bridges`. A generated C array must then be serialized as exactly `223 * sizeof(DialogueNode) = 4,460` bytes before any platform alignment of the enclosing asset.

## 8. Frozen integration disposition

No master-copy conflict was silently resolved. Story and Data agree on the player-facing battle vocabulary used by dialogue (`Staggered`, `Power`, and a 0–100 Resonance presentation), and the 16 live bridge rows agree byte-for-byte. The Gate 2 integration disposition is explicit:

- `DIALOGUE_GRAPH.md` is the singular editable source for all 223 records. Data pins this document's SHA-256, imports all 16 bridge plus 207 nonbridge rows, reserves every DialogueId/StringId, and requires a 4,460-byte generated `DialogueNode` array.
- The five post/follower physical interactions are locked as `0x201E..0x2022`, resolve through literal interaction/placement and route tables, and retain disjoint mandatory, repeat, follower, saved-post, and dirty-post conditions.
- Both tutorial acquisitions are literal: the live name-confirmed bootstrap and `CONTINUE_LOADED_STABLE / CHECKPOINT_AFTER_NAME -> SIM_001` construct the same fresh tutorial owner before input.
- `HelpPromptDef` and the 38-binding/125-item `ProcessUiBindingDef` projection are integrated. The latter fixes the three-item Title order, distinct Name Entry composition, two co-rendered opening-slate pages, executable Pause/Relay/Settings/manual-save views, every save/recovery owner, and every exact process accept token. Exactly eighteen represented global/process-overlay owners admit `scene_id=0`. Its process-static copy registry is the exact 103-row range `0x9F01..0x9F67`; Relay runtime fields/display mappings are exactly 27/68 rows.
- Oren's dirty-post, saved-post, assignment, and pre-Relay repeat routes are typed and truth-table checked in priority order `6 > 5 > 3 > 2`; later prechapter states intentionally have no Oren dialogue.
- `UI_SAVE_FAILED` is acquired as a binary DialogueNode only by the final-hook owner. The five nonfinal save policies use their own process-static prompt/label catalog entries, typed buttons, and zero Dialogue roots; none aliases a Graph StringId.
- During pre-approval integration, the three Rusk foyer bridge rows were explicitly migrated from camera field `0` to `CAMERA_CUE_RUSK_FOYER=0x8607` so the authored foyer composition is data-owned rather than inferred. Data's bridge initializer was migrated in the same change and remains byte-identical. This is the sole bridge-field migration in the Gate 2 lock.

Any future change to a locked ID, exact string, bridge byte, once bit, action xref, or root acquisition requires an explicit lock migration and updated goldens. Adding an unreferenced DialogueNode, a hard-coded root in a controller, or a prose-only fallback is a build failure.
