# Human Trials Google Form Template Updates

## Date: November 1, 2025

## Summary of Changes

Updated the Google Form template for human evaluation trials with two major changes:

### 1. Increased Evaluation Load per Person
- **Changed from:** 20 prompts per evaluator
- **Changed to:** 60 prompts per evaluator
- **Time estimate updated:** 30-45 minutes → 90-120 minutes
- **Form variants adjusted:** 6 variants (20 prompts each) → 2 variants (60 prompts each)
- **Evaluator targets:** 90-120 total evaluations (15-20 per variant) → 20-30 total evaluations (10-15 per variant)

### 2. Added Comprehensive Human Evaluation Metrics

In addition to the existing **Scope Width** (1-6 scale) and **Depth** (1-5 scale) metrics, added the following standard LLM evaluation dimensions:

#### New Metrics Added (Section 2C):

1. **Pedagogical Effectiveness (1-5 scale)**
   - Measures how well the response guides student learning
   - Scale: Ineffective → Poor → Adequate → Good → Excellent

2. **Clarity (1-5 scale)**
   - Measures organization and understandability
   - Scale: Very unclear → Somewhat unclear → Acceptable → Clear → Very clear

3. **Helpfulness (1-5 scale)**
   - Measures whether student can make progress
   - Scale: Not helpful → Minimally helpful → Somewhat helpful → Helpful → Very helpful

4. **Factual Accuracy (1-5 scale + N/A)**
   - Measures technical correctness
   - Scale: Multiple errors → Some errors → Mostly accurate → Accurate → Highly accurate
   - Includes N/A option for cases where evaluator cannot assess

5. **Appropriateness for Student Level (categorical)**
   - Assesses calibration to student understanding
   - Options: Too advanced, Appropriately challenging, Too basic, Mixed

6. **Bias or Assumptions (categorical)**
   - Identifies inappropriate stereotyping or unfounded assumptions
   - Scale: No concerns → Minor assumptions → Moderate concerns → Significant bias

#### Updated Question Numbering:
- Q1: Scope Width Rating (unchanged)
- Q2: Depth Rating (unchanged)
- Q3: Pedagogical Effectiveness (NEW)
- Q4: Clarity (NEW)
- Q5: Helpfulness (NEW)
- Q6: Factual Accuracy (NEW)
- Q7: Appropriateness for Student Level (NEW)
- Q8: Bias or Assumptions (NEW)
- Q9: Socratic pedagogy maintenance (previously Q3)
- Q10: Problem domain adherence (previously Q4)
- Q11: Learning helpfulness (previously Q5)
- Q12: Optional comments (previously Q6)

## Updated Category Balance (per 60-prompt form)
- Socratic Probing: 16 prompts (was 5)
- Adaptive Contextualization: 15 prompts (was 5)
- Feedback & Improvement: 14 prompts (was 4)
- Edge Cases: 8 prompts (was 3)
- Safety Challenges: 6 prompts (was 2)
- Template Examples: 1 prompt (was 1)

## Updated Data Export Format

The CSV export now includes columns for all new metrics (01 through 60):
- `Prompt_XX_Pedagogical_Effectiveness`
- `Prompt_XX_Clarity`
- `Prompt_XX_Helpfulness`
- `Prompt_XX_Factual_Accuracy`
- `Prompt_XX_Appropriateness_Level`
- `Prompt_XX_Bias_Assumptions`

## Updated Analysis Requirements

Automated analysis scripts now need to:
1. Parse and analyze 8 evaluation dimensions (up from 2)
2. Calculate inter-rater reliability across all metrics
3. Create multi-dimensional correlation matrices
4. Identify patterns in bias/assumption ratings
5. Detect optimal metric combinations
6. Generate comprehensive statistical reports

## Timeline Impact

Extended timeline to accommodate larger evaluation load:
- Week 1: Generate 120 responses, create 2 form variants
- Week 2: Pilot test with 5 evaluators (15 prompts)
- Week 3-5: Recruit 20-30 evaluators, deploy forms (extended from 2 weeks)
- Week 6: Close forms, export data
- Week 7-8: Comprehensive analysis (extended from 1 week)

## Rationale for Changes

### Why 60 prompts per person?
- Ensures each of the 120 prompts gets evaluated with sufficient coverage (2 variants)
- Reduces total number of evaluators needed (more feasible for pilot studies)
- Provides richer data per evaluator for analyzing individual rating patterns

### Why add comprehensive metrics?
- **Multi-dimensional assessment**: Captures different aspects of response quality beyond scope and depth
- **Research validity**: Aligns with standard LLM evaluation practices in HCI and NLP research
- **Pedagogical insights**: Separates content quality (scope/depth) from instructional quality (effectiveness/clarity)
- **Safety concerns**: Explicit tracking of bias and accuracy issues
- **Student-centered**: Helpfulness and appropriateness measure real-world utility

### Why these specific metrics?
These 8 metrics represent established dimensions from:
- LLM evaluation literature (accuracy, helpfulness, clarity)
- Educational assessment (pedagogical effectiveness, appropriateness for level)
- AI safety research (bias detection, factual accuracy)
- User experience research (helpfulness, clarity)

## Next Steps

1. **Update analysis scripts** to handle 8-dimensional evaluation data
2. **Refine rubrics** during pilot testing with 5 evaluators
3. **Create visualization tools** for multi-metric correlation analysis
4. **Develop scoring aggregation** methods that weight different metrics appropriately
5. **Test form completion time** to validate 90-120 minute estimate

## File Modified
- `data/human_trials_google_form_template.md` (398 lines → 510 lines)

## Sections Added/Modified
- Form Title: Updated to "Comprehensive Response Assessment"
- Form Description: Updated to mention all evaluation dimensions
- **Section 2C (NEW)**: Additional Human Evaluation Metrics with detailed rubric definitions
- Section 3: Evaluation questions expanded from Q1-Q6 to Q1-Q12
- Response Distribution Strategy: Updated for 60-prompt forms
- Pre-Trial Pilot Testing: Updated timing estimates
- Data Export Format: Added columns for all new metrics
- Automated Analysis Scripts: Expanded requirements
- Timeline Recommendation: Extended to accommodate comprehensive evaluation
