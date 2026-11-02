# Part 18: did it say what you meant? (writer-intent agreement)

**Writer-intent agreement: the writers of the pairs say whether a sentence carries what they meant. This is not validation by AAC users.**

Returns: 20 file(s); writers: P01, P02, P03, P04, P05, P06, P07, P08, P09, P10, P11, P12, P13, P14, P15, P16, P17, P18, P19, P20; 200 of 200 items rated. Items come from the writers' own kept pairs (run hw1, prompt P0, 5 `bare` + 5 `chip1` per writer; declared seeded draw in `annotation/intent_check_sample.json`). CIs: Wilson over items, plus a resample of writers (clusters) because each writer rates 10 items.

## 1. Output matches the variant it was generated from

| channel | writer says it is the intended variant | commits to A or B | says split |
|---|---|---|---|
| all | 49/195 = 25.1% [19.6, 31.7]; writer-cluster CI [18.8, 31.6]; 5 unknown | 59/195 = 30.3% [24.2, 37.0]; writer-cluster CI [23.0, 37.6]; 5 unknown | {'version A': 24, 'something else': 136, 'version B': 35, '(unknown)': 5} |
| chip1 (critical chip given) | 38/97 = 39.2% [30.1, 49.1]; writer-cluster CI [27.6, 51.5]; 3 unknown | 40/97 = 41.2% [32.0, 51.2]; writer-cluster CI [29.3, 53.7]; 3 unknown | {'version A': 18, 'something else': 57, 'version B': 22, '(unknown)': 3} |
| bare (keywords only; reference level) | 11/98 = 11.2% [6.4, 19.0]; writer-cluster CI [5.2, 17.2]; 2 unknown | 19/98 = 19.4% [12.8, 28.3]; writer-cluster CI [10.3, 28.6]; 2 unknown | {'something else': 79, 'version B': 13, '(unknown)': 2, 'version A': 6} |

chip1 - bare difference in match rate: +28.0 pp [writer-cluster 95% +14.8, +42.0]

In `bare` the keywords do not say whether version A or B was meant, so its match rate is a reference level (a model cannot know the intended side), not a failure rate.

## 2. Writer vs judge

| channel | q1 four labels: n, agree, kappa | binary 'matches intended': n, agree, kappa |
|---|---|---|
| all | n=195, 38.5%, kappa=0.243 | n=195, 60.5%, kappa=0.311 |
| chip1 | n=97, 42.3%, kappa=0.269 | n=97, 43.3%, kappa=0.054 |
| bare | n=98, 34.7%, kappa=0.191 | n=98, 77.6%, kappa=0.399 |

Writer x judge (all channels), `writer|judge`: A|A=24, B|B=35, other|A=62, other|B=47, other|other=16, other|unclear=11

The judge labels only the critical dimension; the writer judges the whole message.

## 3. Would you accept it as your message?

| channel | yes | yes or small edit | no | counts | yes when writer says it matches | yes when it does not |
|---|---|---|---|---|---|---|
| all | 1/200 = 0.5% [0.1, 2.8]; writer-cluster CI [0.0, 1.5] | 80/200 = 40.0% [33.5, 46.9]; writer-cluster CI [33.5, 46.0] | 120/200 = 60.0% [53.1, 66.5]; writer-cluster CI [54.0, 66.5] | {'with a small edit': 79, 'no': 120, 'yes': 1} | 1/49 = 2.0% [0.4, 10.7] | 0/146 = 0.0% [0.0, 2.6] |
| chip1 | 0/100 = 0.0% [0.0, 3.7]; writer-cluster CI [0.0, 0.0] | 50/100 = 50.0% [40.4, 59.6]; writer-cluster CI [40.0, 61.0] | 50/100 = 50.0% [40.4, 59.6]; writer-cluster CI [39.0, 60.0] | {'with a small edit': 50, 'no': 50} | 0/38 = 0.0% [0.0, 9.2] | 0/59 = 0.0% [0.0, 6.1] |
| bare | 1/100 = 1.0% [0.2, 5.4]; writer-cluster CI [0.0, 3.0] | 30/100 = 30.0% [21.9, 39.6]; writer-cluster CI [21.0, 39.0] | 70/100 = 70.0% [60.4, 78.1]; writer-cluster CI [61.0, 79.0] | {'no': 70, 'with a small edit': 29, 'yes': 1} | 1/11 = 9.1% [1.6, 37.7] | 0/87 = 0.0% [0.0, 4.2] |

## Per writer

| writer | items | match chip1 | match bare | accept yes |
|---|---|---|---|---|
| P01 | 10 | 1/5 = 20.0% [3.6, 62.4] | 1/5 = 20.0% [3.6, 62.4] | 0/10 = 0.0% [0.0, 27.8] |
| P02 | 10 | 3/5 = 60.0% [23.1, 88.2] | 1/5 = 20.0% [3.6, 62.4] | 0/10 = 0.0% [0.0, 27.8] |
| P03 | 10 | 2/5 = 40.0% [11.8, 76.9] | 2/5 = 40.0% [11.8, 76.9] | 0/10 = 0.0% [0.0, 27.8] |
| P04 | 10 | 1/5 = 20.0% [3.6, 62.4] | 0/5 = 0.0% [0.0, 43.4] | 0/10 = 0.0% [0.0, 27.8] |
| P05 | 10 | 0/5 = 0.0% [0.0, 43.4] | 0/5 = 0.0% [0.0, 43.4] | 0/10 = 0.0% [0.0, 27.8] |
| P06 | 10 | 1/5 = 20.0% [3.6, 62.4] | 0/4 = 0.0% [0.0, 49.0]; 1 unknown | 0/10 = 0.0% [0.0, 27.8] |
| P07 | 10 | 1/5 = 20.0% [3.6, 62.4] | 0/5 = 0.0% [0.0, 43.4] | 0/10 = 0.0% [0.0, 27.8] |
| P08 | 10 | 2/5 = 40.0% [11.8, 76.9] | 1/5 = 20.0% [3.6, 62.4] | 0/10 = 0.0% [0.0, 27.8] |
| P09 | 10 | 4/5 = 80.0% [37.6, 96.4] | 0/5 = 0.0% [0.0, 43.4] | 0/10 = 0.0% [0.0, 27.8] |
| P10 | 10 | 0/5 = 0.0% [0.0, 43.4] | 1/5 = 20.0% [3.6, 62.4] | 0/10 = 0.0% [0.0, 27.8] |
| P11 | 10 | 3/5 = 60.0% [23.1, 88.2] | 1/5 = 20.0% [3.6, 62.4] | 0/10 = 0.0% [0.0, 27.8] |
| P12 | 10 | 4/5 = 80.0% [37.6, 96.4] | 1/5 = 20.0% [3.6, 62.4] | 0/10 = 0.0% [0.0, 27.8] |
| P13 | 10 | 4/5 = 80.0% [37.6, 96.4] | 0/5 = 0.0% [0.0, 43.4] | 0/10 = 0.0% [0.0, 27.8] |
| P14 | 10 | 2/5 = 40.0% [11.8, 76.9] | 0/5 = 0.0% [0.0, 43.4] | 0/10 = 0.0% [0.0, 27.8] |
| P15 | 10 | 1/5 = 20.0% [3.6, 62.4] | 0/5 = 0.0% [0.0, 43.4] | 0/10 = 0.0% [0.0, 27.8] |
| P16 | 10 | 1/4 = 25.0% [4.6, 69.9]; 1 unknown | 2/5 = 40.0% [11.8, 76.9] | 1/10 = 10.0% [1.8, 40.4] |
| P17 | 10 | 4/4 = 100.0% [51.0, 100.0]; 1 unknown | 0/4 = 0.0% [0.0, 49.0]; 1 unknown | 0/10 = 0.0% [0.0, 27.8] |
| P18 | 10 | 1/4 = 25.0% [4.6, 69.9]; 1 unknown | 1/5 = 20.0% [3.6, 62.4] | 0/10 = 0.0% [0.0, 27.8] |
| P19 | 10 | 1/5 = 20.0% [3.6, 62.4] | 0/5 = 0.0% [0.0, 43.4] | 0/10 = 0.0% [0.0, 27.8] |
| P20 | 10 | 2/5 = 40.0% [11.8, 76.9] | 0/5 = 0.0% [0.0, 43.4] | 0/10 = 0.0% [0.0, 27.8] |

## Items where the writer did not say it matches the intended variant (chip1 only)

| item | writer | model | version A | version B | intended | tool wrote | says | accept | judge chose | note |
|---|---|---|---|---|---|---|---|---|---|---|
| ic-2764fe | P01 | gpt-6.1-terra | The soup is probably warm in the kitchen. | The soup is warm in the kitchen. | B | The soup is definitely warm. | something else | no | B | Adds definite certainty and omits the kitchen. |
| ic-6784b1 | P01 | gpt-6.1-terra | The café serves lunch near the station. | Does the café serve lunch near the station? | B | Are we having lunch at the cafe? | something else | no | B | Asks about our lunch rather than the cafe serving lunch. |
| ic-7b904c | P01 | qwen2.5-7b | You turn the lamp off after dinner. | Turn the lamp off after dinner. | A | Tell you to turn the lamp off. | something else | no | B | Reporting fragment; neither statement nor complete instruction. |
| ic-7c2ee8 | P01 | gemma3-4b | The dog may need a walk before dinner. | The dog needs a walk before dinner. | B | I must walk the dog now. | something else | no | B | Assigns the walk to me and changes before dinner to now. |
| ic-95c29d | P02 | llama3.1-8b | Please lower the music in the car. | Lower the music in the car. | B | I like the lower music. | something else | no | B | Preference instead of a request to lower the music. |
| ic-c6ddf3 | P02 | gemma3-4b | I paid the phone bill last week. | I will pay the phone bill next week. | B | I want to pay the bill later. | something else | no | B | Desire to pay later is not the plan to pay next week. |
| ic-09a2f3 | P03 | gemma3-4b | The clinic takes walk-ins on Monday. | Does the clinic take walk-ins on Monday? | A | Tell clinic about walk-ins. | something else | no | other | Instruction to tell the clinic, not whether walk-ins are accepted. |
| ic-59c92c | P03 | llama3.1-8b | I practice guitar in the living room. | My brother practices guitar in the living room. | B | They practice guitar. | something else | no | B | Unspecified they instead of my brother; living room omitted. |
| ic-73f889 | P03 | gpt-6.1-terra | You send the report before lunch today. | The manager sends the report before lunch today. | B | They sent the report. | something else | no | B | Past action with an unnamed doer instead of the manager before lunch. |
| ic-616cec | P04 | qwen2.5-7b | The neighbor feeds our cat this morning. | Does the neighbor feed our cat this morning? | A | I will tell the neighbor to feed the cat. | something else | no | A | A plan to instruct the neighbor replaces a claim about feeding. |
| ic-b1de93 | P04 | qwen2.5-7b | Bring my prescription from the pharmacy. | Please bring my prescription from the pharmacy. | A | Please bring the prescription. | version B | with a small edit | B | Add my and from the pharmacy. |
| ic-f9f287 | P04 | gemma3-4b | Your cousin can enter my room now. | Can your cousin enter my room now? | B | Does my cousin enter the room? | something else | no | B | Changes your cousin to my cousin and permission to usual action. |
| ic-fb2e8d | P04 | llama3.1-8b | Check the rent payment on Tuesday. | Please check the rent payment on Tuesday. | A | I need to check the rent payment. | something else | no | A | A personal need rather than a request to another person. |
| ic-0292cd | P05 | qwen2.5-7b | The taxi may wait outside the main gate. | The taxi waits outside the main gate. | B | I am sure I need to wait for the taxi. | something else | no | B | I wait for the taxi rather than the taxi waiting at the gate. |
| ic-5bb816 | P05 | gpt-6.1-terra | I ask for quiet in the music room. | I do not ask for quiet in the music room. | A | Yes, quiet music. | something else | no | A | Quiet music is not a request for quiet in the music room. |
| ic-6de106 | P05 | llama3.1-8b | My friend saves a seat near the stage. | My friend does not save a seat near the stage. | A | You have a friend in the fifth seat. | something else | no | A | Invents a fifth seat instead of saving a seat near the stage. |
| ic-70144a | P05 | qwen2.5-7b | I use the cream after breakfast. | I do not use the cream after breakfast. | B | I don't have cream for breakfast. | something else | no | B | Cream for breakfast instead of using cream after breakfast. |
| ic-893795 | P05 | gemma3-4b | The ramp is perhaps open near the entrance. | The ramp is open near the entrance. | B | The ramp is sure open. | something else | with a small edit | B | Use the ramp is open near the entrance without sure. |
| ic-362d95 | P06 | llama3.1-8b | The nurse called the clinic yesterday. | The nurse will call the clinic tomorrow. | B | I will call the clinic later. | something else | no | B | Speaker replaces the nurse and tomorrow becomes later. |
| ic-723baa | P06 | qwen2.5-7b | We booked the room last week. | We will book the room next week. | A | I booked the room in the past. | something else | no | A | I replaces we and the date last week is lost. |
| ic-795524 | P06 | gemma3-4b | The driver parked the taxi by the hotel. | The driver will park the taxi by the hotel later. | A | I went to the park and took a taxi. | something else | no | A | Park becomes a place and the taxi action changes. |
| ic-8d4768 | P06 | qwen2.5-7b | My friend brought photos to the party last night. | My friend brings photos to the party tonight. | A | I showed you friend photos from the past. | something else | no | A | I showed old photos instead of my friend bringing them to a party. |
| ic-0582d9 | P07 | llama3.1-8b | I can pay the utility bill this week. | I can't pay the utility bill this week. | A | I will pay the bill. | something else | no | A | A commitment to pay differs from ability this week. |
| ic-24ffe7 | P07 | qwen2.5-7b | I need a ride to the clinic tomorrow. | I don't need a ride to the clinic tomorrow. | B | I am not going to ride to the clinic. | something else | no | B | Not going differs from not needing a ride tomorrow. |
| ic-7a40de | P07 | qwen2.5-7b | I have time to finish the report today. | I don't have time to finish the report today. | B | I did not finish the report. | something else | no | B | Failure to finish in the past differs from lacking time today. |
| ic-cff993 | P07 | gpt-6.1-terra | I lower the music in the car. | You lower the music in the car. | A | I want to lower the music. | something else | no | A | Wishing to lower the music is not lowering it in the car. |
| ic-57f06c | P08 | gemma3-4b | The therapist checked the ramp at the entrance. | The therapist will check the ramp at the entrance later. | A | I used the ramp entrance in the past. | something else | no | A | The therapist checking becomes me using the ramp. |
| ic-699f8d | P08 | llama3.1-8b | The class meets in the upstairs room. | Does the class meet in the upstairs room? | B | Do you have class today? | something else | no | B | Asks about having class today, not where the class meets. |
| ic-fd03f1 | P08 | gemma3-4b | The driver waited beside the hotel yesterday. | The driver waits beside the hotel now. | A | I was a driver at the hotel. | something else | no | A | Changes the driver waiting into me being a driver. |
| ic-6f88fa | P09 | gpt-6.1-terra | The bright light bothers me in the bedroom. | The bright light doesn't bother me in the bedroom. | B | I don’t want a bright light. | something else | no | B | Not wanting a light differs from whether it bothers me. |
| ic-0e58e5 | P10 | gemma3-4b | I prepared lunch in the kitchen this morning. | I will prepare lunch in the kitchen tomorrow morning. | A | I had lunch in the kitchen. | something else | no | A | Eating lunch replaces preparing it and loses the date. |
| ic-29df51 | P10 | gpt-6.1-terra | The screen flashed in the quiet room last night. | The screen flashes in the quiet room now. | A | The screen was in the room. | something else | no | A | Only locates the screen, with no flashing. |
| ic-430bad | P10 | llama3.1-8b | My friend brought photos to the café last night. | My friend brings photos to the café tonight. | B | I will show them photos of my friend later. | something else | no | B | Showing photos of my friend replaces my friend bringing photos. |
| ic-a5225e | P10 | qwen2.5-7b | I guess the chef prepared soup for dinner. | The chef prepared soup for dinner. | B | I am sure the chef made the soup. | something else | with a small edit | B | Remove I am sure and restore for dinner. |
| ic-d43b2e | P10 | gpt-6.1-terra | We served soup in the dining room yesterday. | We serve soup in the dining room now. | A | I had soup in the dining room. | something else | no | A | Eating soup replaces serving it. |
| ic-310eca | P11 | gemma3-4b | Please bring the paint brushes upstairs. | Bring the paint brushes upstairs. | B | Please bring brushes. | version A | with a small edit | A | Specify paint brushes and upstairs. |
| ic-5bf133 | P11 | qwen2.5-7b | I am adjusting the hallway lights now. | I adjusted the hallway lights yesterday. | A | Now adjust lights | something else | no | A | An instruction replaces my ongoing or past action. |
| ic-8d1837 | P12 | llama3.1-8b | Wait by the bus stop. | Please wait by the bus stop. | A | I will wait the bus. | something else | no | A | Changes listener to speaker and needs wait for. |
| ic-3c0429 | P13 | gemma3-4b | The receipt might be in the blue folder. | The receipt is in the blue folder. | A | Maybe I want the receipt folder. | something else | no | A | Uncertainty now concerns wanting a folder, not the receipt location. |
| ic-383796 | P14 | gemma3-4b | You called my brother after lunch. | Did you call my brother after lunch? | A | I want to tell my brother. | something else | no | A | I want to tell replaces you calling. |
| ic-49610c | P14 | gemma3-4b | The teacher posts the new timetable. | The teacher does not post the new timetable. | A | The teacher posted. | something else | with a small edit | A | Use posts the new timetable. |
| ic-74cb2b | P14 | qwen2.5-7b | The clinic has my test results. | The clinic does not have my test results. | B | I do not have the clinic results. | something else | no | B | Changes the subject from clinic to me. |
| ic-02b128 | P15 | gemma3-4b | The rent payment left my account yesterday. | Did the rent payment leave my account yesterday? | B | Will I have to leave to pay my rent? | something else | no | B | Asks about leaving to pay rent, not whether payment left the account. |
| ic-6e58b9 | P15 | gemma3-4b | Your sister saved a seat at dinner. | Did your sister save a seat at dinner? | B | Does my sister need me to save her seat? | something else | no | B | Makes me the seat saver and asks about a need, rather than my sister saving it. |
| ic-78d49a | P15 | llama3.1-8b | The drummer lowered the music during rehearsal. | You lowered the music during rehearsal. | A | They will lower the music rehearsal. | something else | no | A | Changes past lowering during rehearsal to future lowering; rehearsal is misattached. |
| ic-96528c | P15 | qwen2.5-7b | I finished the puzzle in the lounge. | My friend finished the puzzle in the lounge. | A | I will finish the puzzle. | something else | with a small edit | A | Use finished and restore in the lounge. |
| ic-79b0eb | P16 | llama3.1-8b | Move the speaker away from the desk. | Please move the speaker away from the desk. | A | I will move the desk. | something else | no | A | Moves the desk instead of the speaker and changes the request to my plan. |
| ic-a8b9e7 | P16 | gemma3-4b | The team meeting might finish by four. | The team meeting will finish by four. | A | Maybe there will be a team meeting. | something else | no | A | Makes the meeting itself uncertain rather than its finishing by four. |
| ic-ffedb1 | P16 | llama3.1-8b | Confirm the station meeting time today. | Please confirm the station meeting time today. | A | We confirm the meeting time. | something else | no | A | Reports a joint confirmation instead of asking the listener to confirm it. |
| ic-2f378d | P18 | gpt-6.1-terra | Please turn down the kitchen radio. | Turn down the kitchen radio. | B | Turn on the radio. | something else | with a small edit | B | Change on to down and restore kitchen. |
| ic-b91005 | P18 | qwen2.5-7b | The bus stops near my flat. | The bus does not stop near my flat. | A | I am at the bus stop. | something else | no | A | Reports my location instead of the bus stopping near my flat. |
| ic-e44164 | P18 | llama3.1-8b | Our group meets outside the library. | Our group does not meet outside the library. | B | They will not meet the group. | something else | no | B | Makes the group the object of meeting and loses the library location. |
| ic-25e84c | P19 | qwen2.5-7b | The guest respects my personal space. | The guest does not respect my personal space. | B | I do not show guest respect. | something else | no | B | Reverses who gives respect and omits personal space. |
| ic-31b6c6 | P19 | gemma3-4b | You carried the guitar into the studio. | My friend carried the guitar into the studio. | B | They carry a guitar. | something else | with a small edit | B | Specify my friend, use carried, and restore into the studio. |
| ic-5f8932 | P19 | llama3.1-8b | The museum permits visitors to sketch. | The museum does not permit visitors to sketch. | A | We need a museum permit. | something else | no | A | A museum permit is a thing; neither version asks for one. |
| ic-baad16 | P19 | gpt-6.1-terra | You booked the table near the window. | My sister booked the table near the window. | A | You book the table. | something else | with a small edit | A | Use booked and restore near the window. |
| ic-38e2eb | P20 | qwen2.5-7b | The advocate sent the accommodation form. | I sent the accommodation form. | A | They send the form. | something else | with a small edit | A | Specify the advocate, use sent, and restore accommodation. |
| ic-49759f | P20 | qwen2.5-7b | I am tasting the mushroom soup now. | I tasted the mushroom soup yesterday. | A | Now taste the soup. | something else | no | A | Commands the listener to taste instead of describing my tasting. |
| ic-d9eaf2 | P20 | llama3.1-8b | I sent the access request yesterday. | I will send the access request tomorrow. | B | Can you send it later? | something else | no | B | Asks the listener to send something instead of stating my plan. |
