# LinkedIn Post — O*NET Agentic Coverage Dataset

We are releasing a dataset (https://github.com/ravyg/ate-agentic-coverage) that answers a question I kept needing and could never look up: for one specific work task, how much of it can an AI agent actually finish on its own.

It scores all 18,796 O*NET work tasks, across every one of the 23 SOC major groups, from 0 to 1: how much of that task an autonomous agent could complete end to end, with no human stepping in. Each task also carries a short written rationale.

Most AI exposure research asks whether a job could be automated. That blurs a lot. A single job title hides dozens of very different tasks, and exposure arrives task by task, not job by job. This dataset works one level down. 43.7% of tasks score under 0.2, work that still needs a person throughout. 18.8% score 0.8 or higher, work an agent can already carry almost alone. The middle is a genuine spread rather than a cliff, which is itself the finding.

The labels were generated with a language model against a neutral instrument, in one consistent pass across all 18,796 tasks, then checked by hand. Three independent annotators each scored the same 200-task audit sample, blind to the model's answers. The model's ranking reaches a Spearman correlation of 0.884 against the human panel, which is 99.9% of the ceiling set by how much the three annotators agree with each other. So the ordering is about as good as it can get.

One honest caveat. The model runs conservative in absolute terms, scoring tasks 0.147 lower on average than humans do. Rankings are trustworthy as released. If you need calibrated absolute numbers, apply the correction we describe. The method, the agreement statistics, and the script that regenerates every number are in the repo, so you can judge the quality yourself.

It was built as the empirical base for our Agentic Task Exposure work, but stands on its own for anyone studying automation risk, skill demand, human and AI task allocation, or benchmarking agents against real work rather than synthetic tasks.

Dataset: https://github.com/ravyg/ate-agentic-coverage
Hugging Face: https://huggingface.co/datasets/ravishgupta/ate-agentic-coverage
Archival DOI: https://doi.org/10.5281/zenodo.22202518
Paper (Agentic Task Exposure): https://arxiv.org/abs/2604.00186
Validation results and method: https://github.com/ravyg/ate-agentic-coverage/blob/main/validation/RESULTS.md
Companion task to ability mapping (18,796 tasks, 95,330 rows): https://github.com/ravyg/ate-task-ability-dataset
O*NET source taxonomy: https://www.onetcenter.org/database.html

A real thank you to Saket Kumar, Maulik Dang, and Shreeya Sharma for the careful annotation work that made the validation possible.

It's open under CC-BY-4.0, free to use with attribution. If it helps your research, a citation is the best thanks, and a star helps others find it.

More on my work: ravishgupta.me

#OpenData #ONET #LaborEconomics #FutureOfWork #AI #Automation
