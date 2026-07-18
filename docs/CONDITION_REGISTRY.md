# Canonical Condition Registry

Status: Gate 2 implementation contract

Authority: this file is the singular source form for every nonzero `COND_*` value declared by a `*ConditionIdValue` enum in `DATA_SCHEMAS.md`. It is subordinate to `N64GAME_MASTER_SPEC.md` and must remain set-equal with the live data-schema declarations. Narrative descriptions do not add hidden operands, change an expression by caller, or override a row below.

Source snapshot used for this audit:

- `docs/DATA_SCHEMAS.md`: SHA-256 `fc22fd5e260442b01293bf26963363b9b32213bf6d6dbdffdce0b16f976ccb69`, 8,905 lines, 640,036 bytes
- `docs/STORY_AND_TIMING.md`: consulted for objective eras, checkpoint facts, portal behavior, and clean/dirty end-state intent
- `docs/TECHNICAL_ARCHITECTURE.md`: consulted for typed-view ownership, transition selection, save validation, and process-navigation ownership

The hash records the exact input audited; set equality and symbol resolution, not a permanently trusted hash string, are the build invariant. Any later schema edit requires regenerating this audit and updating the hash after all rows still pass.

## 1. Canonical typed DSL

The registry block in Section 3 is machine input. A physical line is one complete row:

```text
COND_ROW(id_symbol,id_value,context_mask,allowed_source_mask,first_instruction,instruction_count,max_stack_depth,expression)
```

Whitespace outside identifiers is insignificant. Hex values are unsigned. Unknown tokens, comments inside a row, duplicate keys, trailing operands, implicit casts, and omitted fields are errors.

### 1.1 Leaf tokens

These are grammar tokens, not prose aliases. Each leaf emits exactly one `COND_PUSH_SOURCE` instruction. Nonconstant leaves always emit `value=0`.

| Token | Exact source / numeric value | Exact `subject_id` | Result type |
|---|---|---|---|
| `K(type,value)` | `CONDITION_SOURCE_CONSTANT / 1` | the resolved `ConditionValueType` numeric value | exactly `type`; instruction `value` is the resolved signed 32-bit literal |
| `F(flag)` | `CONDITION_SOURCE_PROGRESS_FLAG / 2` | resolved locked `StoryFlagIndex` | `BOOL` |
| `O(objective)` | `CONDITION_SOURCE_OBJECTIVE_STATE / 3` | resolved nonzero `ObjectiveId` | `OBJECTIVE_STATE` |
| `P(creature)` | `CONDITION_SOURCE_PARTY_CREATURE / 5` | resolved nonzero `CreatureId` | `BOOL` |
| `Q(index)` | `CONDITION_SOURCE_QUEST_COUNTER / 6` | literal counter index `0..7` | `U8` |
| `D(bit)` | `CONDITION_SOURCE_DESTINATION_BIT / 7` | resolved registered `DestinationBit` | `BOOL` |
| `R(bit)` | `CONDITION_SOURCE_RELAY_PAGE_BITS / 8` | resolved registered `RelayPageBit` | `BOOL` |
| `CP()` | `CONDITION_SOURCE_CHECKPOINT_ID / 9` | `0` | `CHECKPOINT_ID` |
| `BR()` | `CONDITION_SOURCE_BATTLE_RESULT / 10` | `0` | `BATTLE_RESULT` |
| `RD()` | `CONDITION_SOURCE_RUNTIME_DRAFT_STATE / 11` | `0` | `RUNTIME_DRAFT` |
| `TR()` | `CONDITION_SOURCE_TUTORIAL_RESULT_STATE / 12` | `0` | `TUTORIAL_RESULT` |
| `PR()` | `CONDITION_SOURCE_PRE_RUSK_SNAPSHOT_STATE / 13` | `0` | `PRE_RUSK_SNAPSHOT` |
| `MS()` | `CONDITION_SOURCE_SELECTED_MAP_NODE / 14` | `0` | `MAP_SELECTION` |
| `RT()` | `CONDITION_SOURCE_RUNTIME_CHECKPOINT_TOKEN / 15` | `0` | `RUNTIME_CHECKPOINT` |
| `RF()` | `CONDITION_SOURCE_RETURN_FOLLOWER_STATE / 16` | `0` | `RETURN_FOLLOWER` |
| `JS()` | `CONDITION_SOURCE_SELECTED_JOURNAL_SEMANTIC_CLASS / 17` | `0` | `JOURNAL_SEMANTIC` |
| `DI()` | `CONDITION_SOURCE_RUNTIME_DIRTY_STATE / 18` | `0` | `RUNTIME_DIRTY` |
| `FO()` | `CONDITION_SOURCE_FINAL_SAVE_OUTCOME / 19` | `0` | `FINAL_SAVE_OUTCOME` |
| `WA()` | `CONDITION_SOURCE_DIRTY_WARNING_ACK / 20` | `0` | `DIRTY_WARNING_ACK` |
| `CT()` | `CONDITION_SOURCE_CONTROL_STATE / 21` | `0` | `CONTROL_STATE` |
| `PA()` | `CONDITION_SOURCE_PROCESS_ACCEPT_TOKEN / 22` | `0` | `PROCESS_ACCEPT` |
| `OG()` | `CONDITION_SOURCE_OPENING_FINALIZER_GENERATION / 23` | `0` | `OPENING_GENERATION` |
| `SL()` | `CONDITION_SOURCE_RUNTIME_CURRENT_SAVELOC / 24` | `0` | `SAVEABLE_LOCATION_ID` |

Source 4, `CONDITION_SOURCE_CURRENT_SCENE`, is deliberately unused by this opening registry. Location, portal, and transition row ownership already supplies exact source tuples; smuggling caller identity through a scene test is forbidden.

Constant type tokens resolve exactly to the `ConditionValueType` suffix: `BOOL`, `U8`, `OBJECTIVE_STATE`, `CHECKPOINT_ID`, `BATTLE_RESULT`, `RUNTIME_DRAFT`, `TUTORIAL_RESULT`, `PRE_RUSK_SNAPSHOT`, `MAP_SELECTION`, `RUNTIME_CHECKPOINT`, `RETURN_FOLLOWER`, `JOURNAL_SEMANTIC`, `RUNTIME_DIRTY`, `FINAL_SAVE_OUTCOME`, `DIRTY_WARNING_ACK`, `CONTROL_STATE`, `PROCESS_ACCEPT`, `OPENING_GENERATION`, and `SAVEABLE_LOCATION_ID`. A symbolic constant must resolve in the matching enum domain. `K(BOOL,1)` is the only Boolean literal used; no truthy integer conversion exists.

### 1.2 Operators and parentheses

The only expressions are:

```text
NOT(a)
AND(a,b,...)
OR(a,b)
EQ(a,b)
GE(a,b)
```

`NOT` has arity one. `OR`, `EQ`, and `GE` have arity two. `AND` has arity at least two and is exact left association: `AND(a,b,c)` means `AND(AND(a,b),c)`. Commas and parentheses are semantic. There is no precedence outside the explicit syntax.

Compilation is deterministic left-to-right postorder. Children are emitted in written order, followed by the operator. The compiler may not reorder commutative operands, balance an `AND`, fold constants, eliminate duplicate leaves, apply implication knowledge, share a subexpression, or insert a default. `EQ` requires identical operand types. `GE` is legal only for the ordered types allowed by `DATA_SCHEMAS.md`; the rows below use `U8`, `OBJECTIVE_STATE`, and `JOURNAL_SEMANTIC`. Every expression must finish with exactly one `BOOL` stack cell.

### 1.3 Context and source masks

Registry context masks are literal:

| Value | Context | Allowed source whitelist |
|---:|---|---:|
| `0x01` | `CONDITION_CONTEXT_PROGRESS` | `0x000003FF` (sources 1–10) |
| `0x02` | `CONDITION_CONTEXT_TRANSITION` | `0x0010FFFF` (sources 1–16 and 21) |
| `0x04` | `CONDITION_CONTEXT_PROCESS_NAV` | `0x00FFFFFF` (sources 1–24) |
| `0x08` | `CONDITION_CONTEXT_INTERACTION` | `0x0010FFFF` (sources 1–16 and 21) |
| `0x10` | `CONDITION_CONTEXT_SAVE_CODEC` | `0x000003FF` (sources 1–10) |
| `0x20` | `CONDITION_CONTEXT_POST_CHAPTER_INTERACTION` | `0x000603FF` (sources 1–10, 18, and 19) |

A row may use `0x0A` only when the same immutable predicate is called by both transition and interaction ownership. Its source set must fit the intersection of both whitelists. `allowed_source_mask` is not a maximum: it equals exactly the OR of `1u << (source-1)` for leaves present in that row, including source 1 whenever a constant appears.

## 2. Save-condition prerequisite

In save-codec context, every `COND_SAVE_*` row is evaluated only after the candidate `SaveData` has passed the complete opening semantic validator and after the candidate location tuple has resolved by exact equality to the selected `SaveableLocationDef`. The AST still repeats every condition-relevant fact available through the Condition VM while remaining within its 32-instruction cap. `COND_SAVE_SLICE_COMPLETE` is also a legal interaction-context base predicate for post-chapter NPC routing; in that context the immutable live progress view must pass the same complete semantic validator before the row is evaluated, but no EEPROM-success fact is inferred. The dedicated post-chapter saved/dirty rows add the typed outcome and dirty-state distinction.

The semantic validator, not an invented Condition source, proves facts the VM cannot read: exact party count/order/active indices/HP/progression, encounter-clear bit, reward-claim bit, Team Link, exact last encounter, exact current and last-safe tuple, story implications, and checkpoint/save-reason recipe coherence. Failure of that prerequisite is false/fatal validation, never permission to evaluate a weaker condition. This boundary is explicit and identical for encode, decode, Continue, last-safe fallback, manual-save, transition-save, and settings-save validation.

`GE(O(OBJ_FIND_TAVI),K(OBJECTIVE_STATE,OBJECTIVE_ACTIVE))` intentionally means active-or-later within a semantically valid opening record. `OBJECTIVE_FAILED` is not a legal opening state and is rejected before condition evaluation.

## 3. Singular registry

Rows are sorted by unsigned numeric `ConditionId`. The instruction table is a dense concatenation in this order. `first_instruction` is zero-based.

```condition-registry
COND_ROW(COND_DEST_ANNEX_AVAILABLE,0x6101,0x01,0x00000040,0,1,1,D(DESTINATION_ANNEX_BIT))
COND_ROW(COND_DEST_ESTATE_UNLOCKED,0x6102,0x01,0x00000042,1,3,2,AND(D(DESTINATION_ESTATE_BIT),F(FLAG_ESTATE_DESTINATION_UNLOCKED)))
COND_ROW(COND_DEST_ESTATE_ARRIVED,0x6103,0x01,0x00000002,4,1,1,F(FLAG_ESTATE_ARRIVED))
COND_ROW(COND_OBJ_RELAY_ACTIVE,0x6110,0x01,0x00000005,5,3,2,EQ(O(OBJ_RETRIEVE_FIELD_RELAY),K(OBJECTIVE_STATE,OBJECTIVE_ACTIVE)))
COND_ROW(COND_OBJ_RELAY_COMPLETE,0x6111,0x01,0x00000005,8,3,2,EQ(O(OBJ_RETRIEVE_FIELD_RELAY),K(OBJECTIVE_STATE,OBJECTIVE_COMPLETE)))
COND_ROW(COND_OBJ_FIND_TAVI_ACTIVE,0x6112,0x01,0x00000005,11,3,2,EQ(O(OBJ_FIND_TAVI),K(OBJECTIVE_STATE,OBJECTIVE_ACTIVE)))
COND_ROW(COND_OBJ_FIND_TAVI_COMPLETE,0x6113,0x01,0x00000005,14,3,2,EQ(O(OBJ_FIND_TAVI),K(OBJECTIVE_STATE,OBJECTIVE_COMPLETE)))
COND_ROW(COND_OBJ_RETURN_ACTIVE,0x6114,0x01,0x00000005,17,3,2,EQ(O(OBJ_RETURN_WITH_TAVI),K(OBJECTIVE_STATE,OBJECTIVE_ACTIVE)))
COND_ROW(COND_OBJ_RETURN_COMPLETE,0x6115,0x01,0x00000005,20,3,2,EQ(O(OBJ_RETURN_WITH_TAVI),K(OBJECTIVE_STATE,OBJECTIVE_COMPLETE)))
COND_ROW(COND_OBJ_OPENING_ACTIVE,0x6116,0x01,0x00000005,23,3,2,EQ(O(OBJ_OPENING_COMPLETE),K(OBJECTIVE_STATE,OBJECTIVE_ACTIVE)))
COND_ROW(COND_OBJ_OPENING_COMPLETE,0x6117,0x01,0x00000005,26,3,2,EQ(O(OBJ_OPENING_COMPLETE),K(OBJECTIVE_STATE,OBJECTIVE_COMPLETE)))
COND_ROW(COND_TRANS_ALWAYS,0x6201,0x02,0x00000001,29,1,1,K(BOOL,1))
COND_ROW(COND_TRANS_NAME_DRAFT_CONFIRMED,0x6202,0x02,0x00000401,30,3,2,EQ(RD(),K(RUNTIME_DRAFT,RUNTIME_DRAFT_NAME_CONFIRMED)))
COND_ROW(COND_TRANS_TUTORIAL_RESULT_COMPLETE,0x6203,0x02,0x00000801,33,3,2,EQ(TR(),K(TUTORIAL_RESULT,TUTORIAL_RESULT_COMPLETE)))
COND_ROW(COND_TRANS_ANNEX_ONBOARDING_COMPLETE,0x6204,0x02,0x00000002,36,5,2,AND(F(FLAG_TUTORIAL_COMPLETE),F(FLAG_ANNEX_INTRO_COMPLETE),F(FLAG_STARTER_TEAM_RECEIVED)))
COND_ROW(COND_TRANS_ANNEX_FIRST_DEPARTURE_NO_RETURN_FOLLOWER,0x6205,0x0A,0x00008003,41,10,3,AND(F(FLAG_FIELD_RELAY_UNLOCKED),F(FLAG_ESTATE_DESTINATION_UNLOCKED),NOT(F(FLAG_ANNEX_EXIT_CLEARED)),EQ(RF(),K(RETURN_FOLLOWER,RETURN_FOLLOWER_INACTIVE))))
COND_ROW(COND_TRANS_ANNEX_NODE_NO_RETURN_FOLLOWER,0x6206,0x02,0x0000A001,51,7,3,AND(EQ(MS(),K(MAP_SELECTION,MAP_SELECTION_ANNEX)),EQ(RF(),K(RETURN_FOLLOWER,RETURN_FOLLOWER_INACTIVE))))
COND_ROW(COND_TRANS_ESTATE_FIRST_ARRIVAL_NO_RETURN_FOLLOWER,0x6207,0x02,0x0000A003,58,12,3,AND(EQ(MS(),K(MAP_SELECTION,MAP_SELECTION_ESTATE)),F(FLAG_ESTATE_DESTINATION_UNLOCKED),NOT(F(FLAG_ESTATE_ARRIVED)),EQ(RF(),K(RETURN_FOLLOWER,RETURN_FOLLOWER_INACTIVE))))
COND_ROW(COND_TRANS_ESTATE_RESELECT_NO_RETURN_FOLLOWER,0x6208,0x02,0x0000A003,70,9,3,AND(EQ(MS(),K(MAP_SELECTION,MAP_SELECTION_ESTATE)),F(FLAG_ESTATE_ARRIVED),EQ(RF(),K(RETURN_FOLLOWER,RETURN_FOLLOWER_INACTIVE))))
COND_ROW(COND_TRANS_ESTATE_EXIT_NO_RETURN_FOLLOWER,0x6209,0x0A,0x00008003,79,5,3,AND(F(FLAG_ESTATE_ARRIVED),EQ(RF(),K(RETURN_FOLLOWER,RETURN_FOLLOWER_INACTIVE))))
COND_ROW(COND_TRANS_ESTATE_DOOR_OPEN,0x620A,0x02,0x00000002,84,1,1,F(FLAG_ESTATE_DOOR_OPEN))
COND_ROW(COND_TRANS_ORRERY_STAIR_OPEN,0x620B,0x02,0x00000002,85,1,1,F(FLAG_ORRERY_STAIR_OPEN))
COND_ROW(COND_TRANS_RUSK_START,0x620C,0x02,0x00000002,86,4,2,AND(F(FLAG_RUSK_CONFRONTATION_SEEN),NOT(F(FLAG_RUSK_BATTLE_WON))))
COND_ROW(COND_TRANS_PRE_RUSK_SNAPSHOT_VALID,0x620D,0x02,0x00001001,90,3,2,EQ(PR(),K(PRE_RUSK_SNAPSHOT,PRE_RUSK_SNAPSHOT_VALID)))
COND_ROW(COND_TRANS_RETURN_FOLLOWER_ACTIVE,0x620E,0x0A,0x00008001,93,3,2,EQ(RF(),K(RETURN_FOLLOWER,RETURN_FOLLOWER_ACTIVE)))
COND_ROW(COND_TRANS_SLICE_CHECKPOINT_COMMITTED,0x620F,0x02,0x00004001,96,3,2,EQ(RT(),K(RUNTIME_CHECKPOINT,RUNTIME_CHECKPOINT_SLICE_COMPLETE_COMMITTED)))
COND_ROW(COND_TRANS_ANNEX_REPEAT_TRAVEL_NO_RETURN_FOLLOWER,0x6210,0x0A,0x00008003,99,9,3,AND(F(FLAG_FIELD_RELAY_UNLOCKED),F(FLAG_ESTATE_DESTINATION_UNLOCKED),F(FLAG_ANNEX_EXIT_CLEARED),EQ(RF(),K(RETURN_FOLLOWER,RETURN_FOLLOWER_INACTIVE))))
COND_ROW(COND_TRANS_RETURN_FOLLOWER_ACTIVE_ANNEX_SELECTED,0x6211,0x02,0x0000A001,108,7,3,AND(EQ(RF(),K(RETURN_FOLLOWER,RETURN_FOLLOWER_ACTIVE)),EQ(MS(),K(MAP_SELECTION,MAP_SELECTION_ANNEX))))
COND_ROW(COND_TRANS_RETURN_FOLLOWER_ACTIVE_ESTATE_SELECTED,0x6212,0x02,0x0000A001,115,7,3,AND(EQ(RF(),K(RETURN_FOLLOWER,RETURN_FOLLOWER_ACTIVE)),EQ(MS(),K(MAP_SELECTION,MAP_SELECTION_ESTATE))))
COND_ROW(COND_SAVE_AFTER_NAME,0x6301,0x10,0x00000002,122,6,2,AND(F(FLAG_PLAYER_NAME_CONFIRMED),F(FLAG_OPENING_CINEMATIC_SEEN),NOT(F(FLAG_TUTORIAL_COMPLETE))))
COND_ROW(COND_SAVE_ANNEX_STORY_LEGAL,0x6302,0x10,0x00000012,128,9,2,AND(F(FLAG_TUTORIAL_COMPLETE),F(FLAG_ANNEX_INTRO_COMPLETE),F(FLAG_STARTER_TEAM_RECEIVED),P(ECHO_QUARRUNE),P(ECHO_AYSELOR)))
COND_ROW(COND_SAVE_RELAY_ACQUIRED,0x6303,0x10,0x000000B7,137,29,3,AND(F(FLAG_TUTORIAL_COMPLETE),F(FLAG_ANNEX_INTRO_COMPLETE),F(FLAG_STARTER_TEAM_RECEIVED),P(ECHO_QUARRUNE),P(ECHO_AYSELOR),F(FLAG_FIELD_RELAY_QUEST_STARTED),F(FLAG_FIELD_RELAY_UNLOCKED),GE(Q(0),K(U8,2)),R(RELAY_PARTY_BIT),R(RELAY_MESSAGES_BIT),R(RELAY_RESONANCE_BIT),R(RELAY_MAP_BIT),EQ(O(OBJ_RETRIEVE_FIELD_RELAY),K(OBJECTIVE_STATE,OBJECTIVE_ACTIVE))))
COND_ROW(COND_SAVE_TRACE_OR_LATER,0x6304,0x10,0x000000B7,166,31,3,AND(F(FLAG_TUTORIAL_COMPLETE),F(FLAG_ANNEX_INTRO_COMPLETE),F(FLAG_STARTER_TEAM_RECEIVED),P(ECHO_QUARRUNE),P(ECHO_AYSELOR),F(FLAG_FIELD_RELAY_UNLOCKED),GE(Q(0),K(U8,3)),R(RELAY_PARTY_BIT),R(RELAY_MESSAGES_BIT),R(RELAY_RESONANCE_BIT),R(RELAY_MAP_BIT),F(FLAG_TAVI_MISSING_REPORTED),F(FLAG_ESTATE_DESTINATION_UNLOCKED),GE(O(OBJ_FIND_TAVI),K(OBJECTIVE_STATE,OBJECTIVE_ACTIVE))))
COND_ROW(COND_SAVE_ANNEX_RETURNED,0x6305,0x10,0x00000017,197,25,3,AND(F(FLAG_TUTORIAL_COMPLETE),F(FLAG_ANNEX_INTRO_COMPLETE),F(FLAG_STARTER_TEAM_RECEIVED),P(ECHO_QUARRUNE),P(ECHO_AYSELOR),F(FLAG_ESTATE_DOOR_OPEN),F(FLAG_ORRERY_STAIR_OPEN),F(FLAG_IVO_MET),F(FLAG_TAVI_FOUND),F(FLAG_RETURN_TO_ANNEX_REQUESTED),F(FLAG_TAVI_RETURNED_TO_ANNEX),EQ(O(OBJ_RETURN_WITH_TAVI),K(OBJECTIVE_STATE,OBJECTIVE_COMPLETE))))
COND_ROW(COND_SAVE_SLICE_COMPLETE,0x6306,0x18,0x00000317,222,31,3,AND(F(FLAG_TUTORIAL_COMPLETE),F(FLAG_ANNEX_INTRO_COMPLETE),F(FLAG_STARTER_TEAM_RECEIVED),P(ECHO_QUARRUNE),P(ECHO_AYSELOR),F(FLAG_RUSK_BATTLE_WON),F(FLAG_TAVI_RETURNED_TO_ANNEX),F(FLAG_SOLACE_BEACON_RECEIVED),F(FLAG_FRACTURE_SIGNAL_SEEN),F(FLAG_SLICE_COMPLETE),EQ(O(OBJ_OPENING_COMPLETE),K(OBJECTIVE_STATE,OBJECTIVE_COMPLETE)),EQ(CP(),K(CHECKPOINT_ID,CHECKPOINT_SLICE_COMPLETE)),EQ(BR(),K(BATTLE_RESULT,BATTLE_RESULT_WIN))))
COND_ROW(COND_SAVE_THRESHOLD_DEPARTURE,0x6307,0x10,0x00000307,253,24,4,OR(AND(F(FLAG_ANNEX_EXIT_CLEARED),GE(O(OBJ_FIND_TAVI),K(OBJECTIVE_STATE,OBJECTIVE_ACTIVE))),AND(EQ(CP(),K(CHECKPOINT_ID,CHECKPOINT_RUSK_RETURN_TO_ANNEX)),EQ(BR(),K(BATTLE_RESULT,BATTLE_RESULT_RETURN_TO_ANNEX)),F(FLAG_ESTATE_ARRIVED),F(FLAG_RUSK_CONFRONTATION_SEEN),NOT(F(FLAG_RUSK_BATTLE_WON)),EQ(O(OBJ_FIND_TAVI),K(OBJECTIVE_STATE,OBJECTIVE_ACTIVE)))))
COND_ROW(COND_SAVE_ESTATE_ARRIVED,0x6308,0x10,0x00000007,277,5,3,AND(F(FLAG_ESTATE_ARRIVED),GE(O(OBJ_FIND_TAVI),K(OBJECTIVE_STATE,OBJECTIVE_ACTIVE))))
COND_ROW(COND_SAVE_ESTATE_POST_RUSK,0x6309,0x10,0x00000217,282,19,3,AND(F(FLAG_ESTATE_ARRIVED),F(FLAG_RUSK_BATTLE_WON),F(FLAG_RUSK_BATTLE_REWARD_CLAIMED),F(FLAG_ESTATE_DOOR_OPEN),EQ(BR(),K(BATTLE_RESULT,BATTLE_RESULT_WIN)),P(ECHO_QUARRUNE),P(ECHO_AYSELOR),GE(O(OBJ_FIND_TAVI),K(OBJECTIVE_STATE,OBJECTIVE_ACTIVE))))
COND_ROW(COND_SAVE_ESTATE_INTERIOR,0x630A,0x10,0x00000217,301,19,3,AND(F(FLAG_ESTATE_ARRIVED),F(FLAG_RUSK_BATTLE_WON),F(FLAG_RUSK_BATTLE_REWARD_CLAIMED),F(FLAG_ESTATE_DOOR_OPEN),EQ(BR(),K(BATTLE_RESULT,BATTLE_RESULT_WIN)),P(ECHO_QUARRUNE),P(ECHO_AYSELOR),GE(O(OBJ_FIND_TAVI),K(OBJECTIVE_STATE,OBJECTIVE_ACTIVE))))
COND_ROW(COND_SAVE_ORRERY_OPEN,0x630B,0x10,0x00000217,320,21,3,AND(F(FLAG_ESTATE_ARRIVED),F(FLAG_RUSK_BATTLE_WON),F(FLAG_RUSK_BATTLE_REWARD_CLAIMED),F(FLAG_ESTATE_DOOR_OPEN),EQ(BR(),K(BATTLE_RESULT,BATTLE_RESULT_WIN)),P(ECHO_QUARRUNE),P(ECHO_AYSELOR),GE(O(OBJ_FIND_TAVI),K(OBJECTIVE_STATE,OBJECTIVE_ACTIVE)),F(FLAG_ORRERY_STAIR_OPEN)))
COND_ROW(COND_SAVE_TAVI_FOUND,0x630C,0x10,0x00000217,341,30,3,AND(F(FLAG_ESTATE_ARRIVED),F(FLAG_RUSK_BATTLE_WON),F(FLAG_RUSK_BATTLE_REWARD_CLAIMED),F(FLAG_ESTATE_DOOR_OPEN),F(FLAG_ORRERY_STAIR_OPEN),F(FLAG_IVO_MET),F(FLAG_TAVI_FOUND),F(FLAG_RETURN_TO_ANNEX_REQUESTED),NOT(F(FLAG_TAVI_RETURNED_TO_ANNEX)),EQ(O(OBJ_RETURN_WITH_TAVI),K(OBJECTIVE_STATE,OBJECTIVE_ACTIVE)),P(ECHO_QUARRUNE),P(ECHO_AYSELOR),EQ(BR(),K(BATTLE_RESULT,BATTLE_RESULT_WIN))))
COND_ROW(COND_PROC_ALWAYS,0x6401,0x04,0x00000001,371,1,1,K(BOOL,1))
COND_ROW(COND_PROC_NEW_GAME_ACCEPTED,0x6402,0x04,0x00200401,372,7,3,AND(EQ(PA(),K(PROCESS_ACCEPT,PROCESS_ACCEPT_NEW_GAME)),EQ(RD(),K(RUNTIME_DRAFT,RUNTIME_DRAFT_NEW_GAME_ACCEPTED))))
COND_ROW(COND_PROC_OPENING_FINALIZED,0x6403,0x04,0x00600401,379,11,3,AND(EQ(PA(),K(PROCESS_ACCEPT,PROCESS_ACCEPT_OPENING_FINISH)),EQ(OG(),K(OPENING_GENERATION,OPENING_FINALIZER_GENERATION_CURRENT)),EQ(RD(),K(RUNTIME_DRAFT,RUNTIME_DRAFT_OPENING_FINALIZED))))
COND_ROW(COND_PROC_NAME_DRAFT_CONFIRMED,0x6404,0x04,0x00200401,390,7,3,AND(EQ(PA(),K(PROCESS_ACCEPT,PROCESS_ACCEPT_NAME_CONFIRM)),EQ(RD(),K(RUNTIME_DRAFT,RUNTIME_DRAFT_NAME_CONFIRMED))))
COND_ROW(COND_PROC_NAME_DRAFT_UNCOMMITTED,0x6405,0x04,0x00200401,397,7,3,AND(EQ(PA(),K(PROCESS_ACCEPT,PROCESS_ACCEPT_NAME_CANCEL_RETURN)),EQ(RD(),K(RUNTIME_DRAFT,RUNTIME_DRAFT_OPENING_FINALIZED))))
COND_ROW(COND_PROC_VALID_CONTINUE_PAGE,0x6406,0x04,0x00210001,404,7,3,AND(EQ(PA(),K(PROCESS_ACCEPT,PROCESS_ACCEPT_TITLE_CONTINUE)),GE(JS(),K(JOURNAL_SEMANTIC,JOURNAL_SEMANTIC_VALID_GENERAL))))
COND_ROW(COND_PROC_STABLE_GAMEPLAY_CLEAN,0x6407,0x04,0x00320001,411,11,3,AND(EQ(PA(),K(PROCESS_ACCEPT,PROCESS_ACCEPT_RETURN_TO_TITLE)),EQ(CT(),K(CONTROL_STATE,CONTROL_STATE_STABLE)),EQ(DI(),K(RUNTIME_DIRTY,RUNTIME_PROGRESS_CLEAN))))
COND_ROW(COND_PROC_END_CARD_SAVED,0x6408,0x04,0x00860001,422,11,3,AND(EQ(FO(),K(FINAL_SAVE_OUTCOME,FINAL_SAVE_OUTCOME_SAVED)),EQ(DI(),K(RUNTIME_DIRTY,RUNTIME_PROGRESS_CLEAN)),EQ(SL(),K(SAVEABLE_LOCATION_ID,SAVELOC_ANNEX_ATRIUM_POST_CHAPTER))))
COND_ROW(COND_PROC_END_CARD_DIRTY_RESOLVED,0x6409,0x04,0x00860001,433,11,3,AND(EQ(FO(),K(FINAL_SAVE_OUTCOME,FINAL_SAVE_OUTCOME_CONTINUE_UNSAVED)),EQ(DI(),K(RUNTIME_DIRTY,RUNTIME_PROGRESS_DIRTY)),EQ(SL(),K(SAVEABLE_LOCATION_ID,SAVELOC_ANNEX_ATRIUM_POST_CHAPTER))))
COND_ROW(COND_PROC_END_CARD_DIRTY_RETURN_CONFIRMED,0x640A,0x04,0x00AE0001,444,19,3,AND(EQ(FO(),K(FINAL_SAVE_OUTCOME,FINAL_SAVE_OUTCOME_CONTINUE_UNSAVED)),EQ(DI(),K(RUNTIME_DIRTY,RUNTIME_PROGRESS_DIRTY)),EQ(SL(),K(SAVEABLE_LOCATION_ID,SAVELOC_ANNEX_ATRIUM_POST_CHAPTER)),EQ(PA(),K(PROCESS_ACCEPT,PROCESS_ACCEPT_RETURN_TO_TITLE)),EQ(WA(),K(DIRTY_WARNING_ACK,DIRTY_WARNING_END_CARD_RETURN_ACK))))
COND_ROW(COND_PROC_STABLE_GAMEPLAY_DIRTY_RETURN_CONFIRMED,0x640B,0x04,0x003A0001,463,15,3,AND(EQ(PA(),K(PROCESS_ACCEPT,PROCESS_ACCEPT_RETURN_TO_TITLE)),EQ(CT(),K(CONTROL_STATE,CONTROL_STATE_STABLE)),EQ(DI(),K(RUNTIME_DIRTY,RUNTIME_PROGRESS_DIRTY)),EQ(WA(),K(DIRTY_WARNING_ACK,DIRTY_WARNING_GAMEPLAY_RETURN_ACK))))
COND_ROW(COND_PROC_ROLLBACK_FATAL_RETRY_READY,0x640C,0x04,0x00000001,478,1,1,K(BOOL,1))
COND_ROW(COND_PROC_ROLLBACK_FATAL_RETURN_CLEAN,0x640D,0x04,0x00220001,479,7,3,AND(EQ(PA(),K(PROCESS_ACCEPT,PROCESS_ACCEPT_RETURN_TO_TITLE)),EQ(DI(),K(RUNTIME_DIRTY,RUNTIME_PROGRESS_CLEAN))))
COND_ROW(COND_PROC_ROLLBACK_FATAL_DIRTY_RETURN_CONFIRMED,0x640E,0x04,0x002A0001,486,11,3,AND(EQ(PA(),K(PROCESS_ACCEPT,PROCESS_ACCEPT_RETURN_TO_TITLE)),EQ(DI(),K(RUNTIME_DIRTY,RUNTIME_PROGRESS_DIRTY)),EQ(WA(),K(DIRTY_WARNING_ACK,DIRTY_WARNING_ROLLBACK_FATAL_RETURN_ACK))))
COND_ROW(COND_PROC_NEW_GAME_ABORT_READY,0x640F,0x04,0x00200401,497,7,3,AND(EQ(PA(),K(PROCESS_ACCEPT,PROCESS_ACCEPT_NEW_GAME_ABORT_TO_TITLE)),EQ(RD(),K(RUNTIME_DRAFT,RUNTIME_DRAFT_NAME_CONFIRMED))))
COND_ROW(COND_INTERACT_ORRERY_CLOSED,0x6501,0x08,0x00000002,504,2,1,NOT(F(FLAG_ORRERY_STAIR_OPEN)))
COND_ROW(COND_INTERACT_ORRERY_OPEN,0x6502,0x08,0x00000002,506,1,1,F(FLAG_ORRERY_STAIR_OPEN))
COND_ROW(COND_NPC_MARA_POST,0x6530,0x01,0x00000005,507,3,2,GE(O(OBJ_FIND_TAVI),K(OBJECTIVE_STATE,OBJECTIVE_ACTIVE)))
COND_ROW(COND_NPC_MARA_PRE,0x6531,0x01,0x00000005,510,4,2,NOT(GE(O(OBJ_FIND_TAVI),K(OBJECTIVE_STATE,OBJECTIVE_ACTIVE))))
COND_ROW(COND_NPC_JO_POST,0x6532,0x01,0x00000002,514,1,1,F(FLAG_FIELD_RELAY_UNLOCKED))
COND_ROW(COND_NPC_JO_PRE,0x6533,0x01,0x00000002,515,2,1,NOT(F(FLAG_FIELD_RELAY_UNLOCKED)))
COND_ROW(COND_NPC_PELL_POST,0x6534,0x01,0x00000002,517,1,1,F(FLAG_ESTATE_DESTINATION_UNLOCKED))
COND_ROW(COND_NPC_PELL_PRE,0x6535,0x01,0x00000002,518,2,1,NOT(F(FLAG_ESTATE_DESTINATION_UNLOCKED)))
COND_ROW(COND_PORTAL_EXIT_LOCKED_NO_RELAY,0x6536,0x08,0x00000002,520,2,1,NOT(F(FLAG_FIELD_RELAY_UNLOCKED)))
COND_ROW(COND_PORTAL_EXIT_LOCKED_NO_TRACE,0x6537,0x08,0x00000002,522,4,2,AND(F(FLAG_FIELD_RELAY_UNLOCKED),NOT(F(FLAG_ESTATE_DESTINATION_UNLOCKED))))
COND_ROW(COND_NPC_POST_CHAPTER_SAVED,0x6538,0x20,0x00040003,526,5,3,AND(F(FLAG_SLICE_COMPLETE),EQ(FO(),K(FINAL_SAVE_OUTCOME,FINAL_SAVE_OUTCOME_SAVED))))
COND_ROW(COND_NPC_POST_CHAPTER_DIRTY,0x6539,0x20,0x00060003,531,9,3,AND(F(FLAG_SLICE_COMPLETE),EQ(FO(),K(FINAL_SAVE_OUTCOME,FINAL_SAVE_OUTCOME_CONTINUE_UNSAVED)),EQ(DI(),K(RUNTIME_DIRTY,RUNTIME_PROGRESS_DIRTY))))
COND_ROW(COND_NPC_OREN_REPEAT,0x653A,0x08,0x00000002,540,4,2,AND(F(FLAG_FIELD_RELAY_QUEST_STARTED),NOT(F(FLAG_FIELD_RELAY_UNLOCKED))))
```

The follower-return rows are deliberately three different programs. `COND_TRANS_RETURN_FOLLOWER_ACTIVE` is follower-only for Estate-skimmer selection and the Estate-to-map handoff. `_ANNEX_SELECTED` and `_ESTATE_SELECTED` add their exact map selection. A caller may not reinterpret `0x620E` based on a destination or TransitionId.

The two threshold portal-lock rows are also explicit. `NO_RELAY` is exactly Relay false. `NO_TRACE` is exactly Relay true and Estate unlock false. Together with the first-departure and repeat conditions, they are exhaustive and disjoint over semantically valid opening progress.

The two post-chapter NPC rows are disjoint by durable final outcome. `COND_NPC_POST_CHAPTER_SAVED` is true for both legal `SAVED+CLEAN` and `SAVED+DIRTY`: a newer unsaved location/settings mutation does not erase the already verified opening record, so its recorded copy remains truthful. `COND_NPC_POST_CHAPTER_DIRTY` requires the only unsaved-opening pair, `CONTINUE_UNSAVED+DIRTY`, and never implies EEPROM success. `CONTINUE_UNSAVED+CLEAN` is rejected by the save-service state contract before this view can be built. `COND_NPC_OREN_REPEAT` is an interaction-owned pre-acquisition repeat route and is exactly Relay quest started with Relay unlocked false. It cannot replay Oren's stale `Retrieve the Relay` copy after acquisition. Physical NPC/zone availability and stable-control route flags remain separate typed prerequisites.

## 4. Emission contract

For each row, emit one `ConditionDef` with the seven literal fields shown and `reserved=0`. Emit its postorder `ConditionInstr` slice into the single dense instruction table.

Canonical field bytes use N64 big-endian order for multi-byte values:

- `ConditionInstr`: `op:u8`, `source:u8`, `subject_id:u16be`, `value:i32be`; exactly 8 bytes.
- `ConditionDef`: `id:u16be`, `first_instruction:u16be`, `instruction_count:u16be`, `max_stack_depth:u8`, `context_mask:u8`, `allowed_source_mask:u32be`, `reserved:u32be`; exactly 16 bytes.

Operator instructions set `source=0`, `subject_id=0`, and `value=0`. Leaf and operator opcodes are the exact `ConditionOp` numeric values in `DATA_SCHEMAS.md`. Symbolic IDs and constants are resolved before packing; truncation is forbidden.

The compiler must emit:

- exactly 69 `ConditionDef` rows = 1,104 bytes;
- exactly 544 `ConditionInstr` rows = 4,352 bytes;
- exactly 5,456 canonical bytes across both tables;
- instruction indices `0..543`, with no gap, overlap, orphan, or trailing instruction.

## 5. Required generator and validator

Gate 3's condition compiler/validator must perform all of these checks in one failing build step:

1. Parse every `typedef enum *ConditionIdValue` block in the live data schema. Collect every nonzero `COND_*` declaration, including declarations added in a new enum family. Require exact symbol/value set equality with the 69 registry rows. Reject missing, extra, duplicate-symbol, duplicate-value, zero, and alias rows.
2. Parse only the fenced `condition-registry` block with the grammar above. Require one physical row per condition and ascending unsigned ID order.
3. Resolve every flag, objective, creature, destination bit, Relay bit, checkpoint, battle result, runtime enum, and saveable-location symbol against the live generated ID registries. Reject unresolved, wrong-domain, zero-forbidden, tombstoned, and numerically aliased symbols.
4. Build a fresh AST per row. Condition references and named composite-expression references are illegal, so an AST cannot call another condition. Reject any reference token; if future syntax adds named expressions, require a dependency graph and reject all cycles before expansion.
5. Type-check every leaf and operator. Reject illegal `GE`, mismatched `EQ`, non-Boolean logical operands, wrong arity, illegal literals, stack underflow/overflow, and any terminal stack other than exactly one `BOOL`.
6. Emit strict left-to-right postorder without optimization. Recompute and byte-compare `first_instruction`, `instruction_count`, `max_stack_depth`, `context_mask`, and exact used-source mask to the literal row fields.
7. Require each count in `1..32`, each computed peak in `1..8`, and the aggregate count at most 2,048. Widen all range arithmetic before bounds checks.
8. Require context masks to use only `0x3F`. Require the exact used-source mask to be a subset of every context whitelist named by the row. A runtime-only source in a save/progress row is fatal; sources 18 and 19 are legal for NPC selection only under the dedicated `0x20` context.
9. Produce generated C initializers plus independently packed big-endian expected buffers. Reparse the generated initializers into field tuples, repack them, and byte-compare both complete `ConditionDef` and `ConditionInstr` buffers against a fresh compile of the registry. Report the first differing row, field, byte offset, expected value, and actual value.
10. Compile the generated C with warnings as errors and run host VM tests. For every row, test one satisfying view and targeted single-leaf mutations that make the predicate false where logically possible. Add boundary tests for `GE`, stale runtime producers, absent source owners, all three follower-selection rows, both threshold portal rows, NPC complements, the saved/dirty post-chapter split, every save location family, and every clean/dirty process branch.

Runtime evaluation remains fail-closed. An absent or stale generation-bound producer rejects the entire condition before VM execution; an invalid instruction range, source, type, operator, or stack state records a debug fault and returns false.

## 6. Mechanical audit result

The audited schema declares nine `*ConditionIdValue` enum families:

| Enum family | Nonzero rows |
|---|---:|
| `DestinationConditionIdValue` | 3 |
| `ObjectiveConditionIdValue` | 8 |
| `TransitionConditionIdValue` | 18 |
| `SaveLocationConditionIdValue` | 12 |
| `ProcessNavigationConditionIdValue` | 15 |
| `OrreryInteractionConditionIdValue` | 2 |
| `OpeningNpcVariantConditionIdValue` | 6 |
| `OpeningPortalConditionIdValue` | 2 |
| `OpeningNpcInteractionConditionIdValue` | 3 |
| **Total** | **69** |

Audit results:

- declared symbols: 69; unique symbols: 69; unique numeric IDs: 69;
- registry rows: 69; missing: 0; extra: 0;
- dense instruction rows: 544; final exclusive index: 544;
- largest condition: 31 instructions (`COND_SAVE_TRACE_OR_LATER` and `COND_SAVE_SLICE_COMPLETE`), below the 32-row cap;
- largest computed stack: 4 cells (`COND_SAVE_THRESHOLD_DEPARTURE`), below the 8-cell cap;
- context distribution: 17 progress-only, 14 transition-only, 4 transition-plus-interaction, 15 process-only, 11 save-codec-only, 1 save-codec-plus-interaction, 5 interaction-only, and 2 post-chapter-interaction-only;
- every row terminates with one `BOOL`; every literal range is contiguous and nonoverlapping;
- no caller-dependent condition meaning remains; the former follower-selection ambiguity is represented by `0x620E`, `0x6211`, and `0x6212`;
- the saved and unsaved post-chapter Oren rows are mutually exclusive by durable outcome; SAVED admits either dirty state while CONTINUE_UNSAVED requires DIRTY, and the ordinary Oren repeat row cannot survive Relay unlock;
- no unresolved contradiction remains in the audited 69-row condition set.

This is a preproduction data contract, not evidence that the runtime generator, VM, host tests, target ROM, saves, or gameplay have been implemented. Those proofs begin in later production gates.
