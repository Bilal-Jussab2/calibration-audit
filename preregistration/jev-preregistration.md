# Does Jev's confidence mean what it says?

**A pre-registered test of a calibration claim**

Bilal Jussab, Korbant (audit.korbant.co.uk)
Written 22 September 2026, before any of the test data below has been sent to Jev.

## Why this test

On 16 September TypeSafe AI released Jev, a model that makes typed decisions for software instead of writing text. Every answer comes with a probability for each option and a separate confidence score. TypeSafe trained it with a method it calls Reinforcement Learning for Calibrated Decisions, and it describes the result plainly: higher confidence means higher accuracy, and an answer given at 80% should be right about 80% of the time.

That promise matters more for Jev than for most models. Jev is built to sit inside other software, and the obvious way to use it is to let high confidence answers go straight through and send low confidence ones to a person. If the confidence is honest, that works. If it is not, the errors pass through unchecked.

As far as I can find, nobody has published a reliability curve, a calibration error figure or a paper that shows whether the claim holds. So I am going to measure it, and I am writing down exactly how before I see a single result.

## The data

I use two public datasets, both fixed by checksum so anyone can confirm they are testing the same files.

| Dataset | Role | Items | Licence | SHA-256 |
|---|---|---|---|---|
| BANKING77, test split | Main test | 3,080 (77 intents, 40 each) | CC BY 4.0 | `d12d6e3bc4c3103966ae786dc435913c0c563dfa328f5a3646d0e62cfeeb474d` |
| CLINC150, out of scope test set | Second test | 1,000 | CC BY 3.0 | `36923c3705a59e08fe9c3883d8bc2dd966ef93e22cb78ac41171782a698d56e0` (file data_full.json) |

BANKING77 comes from github.com/PolyAI-LDN/task-specific-datasets and CLINC150 from github.com/clinc/oos-eval. BANKING77 is customer service routing, which is the kind of task TypeSafe uses in its own demos. Every item is used and none are removed.

## How Jev is asked

Each utterance goes to Jev in its own request. The only options it can choose from are the dataset's intent labels, spelled exactly as they appear in the dataset. The request, including any instruction text, is fixed before the first scored call and will be published word for word. I will not tune it on the test data.

I will record the model version the API reports and the dates of every run. A failed call is retried up to three times, and anything that still fails is listed in the results rather than quietly left out.

Before this document is committed I will only send Jev made up inputs, to check that the API works and how many options one request can hold.

## What counts as correct

An answer is correct only if the label Jev picks is exactly the dataset's label. Nothing else is cleaned up or matched loosely. I state this first because in earlier work I found that the choice of matching rule alone can move an accuracy figure by more than ten points.

## What I measure

Jev gives two signals that could be read as confidence: the probability on the option it chose, and its separate confidence score. I report both, side by side, because there is no guarantee they behave the same way.

For each signal I sort all 3,080 answers by confidence and split them into ten groups of equal size (ties are kept in dataset order). For each group I compare the average confidence with the share that were actually correct, with a 95% Wilson interval around that share. With 308 answers per group, a group that is about 90% accurate is pinned down to roughly 3.4 points either way.

From those groups I report accuracy, expected calibration error (the average gap between confidence and accuracy, weighted by group size), the largest single gap, the Brier score, a reliability diagram, and the share of answers given at 0.90 or above that turn out to be wrong.

## The pass mark

I decided this before seeing any output. For the chosen option's probability, Jev's claim is **supported** on this test if all three of these hold:

1. Expected calibration error is 0.05 or lower.
2. No group is overconfident by a clear margin, meaning no group's whole 95% interval sits more than 5 points below its average confidence.
3. Confidence actually separates right from wrong: the most confident group's accuracy interval lies entirely above the least confident group's.

The third condition tests TypeSafe's own wording directly. It also stops a model from passing by giving every answer the same confidence equal to its overall accuracy, which would score well on calibration error while telling you nothing.

The separate confidence score is judged by the same rule and reported on its own.

## Being fair about label errors

Ying and Thomas (2022) estimated that about 14% of BANKING77's training examples may be mislabelled. Nobody has measured the test split. A wrong label makes a correct, confident answer look like a confident mistake, which would make Jev look less calibrated than it really is.

So the headline figures are always scored against the original labels, untouched. Then every answer given at 0.90 or above that was marked wrong is checked by hand and sorted as a model error, a label error, or genuinely ambiguous. That list is published in full, and a second set of figures using the corrected labels sits next to the headline, never in place of it.

The verdict follows from both:

| Original labels | Corrected labels | Verdict |
|---|---|---|
| Passes | Passes | Supported |
| Fails | Passes | Inconclusive, because the failure comes from label errors |
| Fails | Fails | Not supported on this test |

If the intervals are too wide to tell either way, the verdict is inconclusive. I would rather say that than overstate a result in either direction.

## The second test: when no option fits

I give Jev the 1,000 CLINC150 utterances that belong to none of its 150 intents, and offer only those 150 intents as choices. Every answer is wrong by design, so a well calibrated model should show low confidence. I report how confidence is spread across these answers and what share come back at 0.90 or above. This part is reported, not scored.

## Limits I know about

Both datasets have been public since 2019 and 2020, so Jev may have seen them in training. That could make its accuracy look better than it would on new data. I cannot correct for it, so I am saying it up front.

This is one kind of task, intent classification, in one language, English. It says nothing about how Jev behaves on anything else.

TypeSafe's documentation describes its calibration as holding across groups of answers rather than for each answer individually. Grouped calibration error is exactly that kind of measure, so this test checks the claim in the form TypeSafe makes it.

## What gets published

The code, the exact request, every raw response, the scored tables, the figures, the hand review list and any failed calls. Anyone with API access should be able to run it again and get the same numbers.

## Right of reply

TypeSafe will get the results at least seven days before they are published, with an offer to include their response in full. Any correction after publication is added with a date.

## Changes after this is committed

If anything here changes after the commit date, the change is added below with the date and the reason. Nothing above will be edited in place.

**Amendments:**

1. 26 September 2026. A correction to the background, not to the method. Under "Why this test" I wrote that, as far as I could find, nobody had published a reliability curve, a calibration error figure or a paper showing whether the claim holds. That was already wrong when I wrote it. JourdanLabs published ASSAY-001 on 18 September 2026 ([donttrustme.ai/assay-001.html](https://donttrustme.ai/assay-001.html)), a pre-registered calibration test of Jev on BANKING77 and CLINC150, reporting a calibration error of 0.0936 on BANKING77 and 0.0204 on CLINC150. My search missed it. Nothing in the data, method, pass mark or analysis above has changed. The results write-up cites ASSAY-001 and compares the two.
