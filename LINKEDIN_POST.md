# LinkedIn Post — O*NET Agentic Coverage Dataset

I'm releasing a dataset that answers a narrower question than most AI-and-work research asks: not "could an AI do this kind of job," but for one specific task, how much of it could an autonomous agent finish end to end, with no human stepping in at all.

It covers all 18,796 O*NET work tasks, the full task corpus, across every occupation. Each task gets a coverage score from 0 to 1: how much of it a current agent could complete alone, unaided, from start to finish. 43.7% of tasks score under 0.2, work that still needs a human throughout. Another 18.8% score 0.8 or higher, work an agent can already do almost entirely on its own. The middle is a real spread, not a cliff, which is the more useful finding: automation exposure isn't binary at the task level.

We didn't just trust the model. Three independent annotators each rated the same 200-task sample by hand, blind to the model's scores. The model's rankings reach a Spearman correlation of 0.884 against the human panel, which is 99.9% of the ceiling set by how much the three humans agree with each other. So the ordering is about as good as it can get. But the model runs conservative in absolute terms: it scores tasks 0.147 lower on average than humans do. Ranking is trustworthy out of the box; anyone who needs calibrated absolute numbers should apply the correction we describe in the repo.

This is useful for labor-economics research, AI-exposure modeling, task-level automation studies, human-AI task allocation work, and benchmarking agent capability against real work tasks rather than synthetic ones.

A real thank you to Saket Kumar, Maulik Dang, and Shreeya Sharma for the careful, independent annotation work that made the validation possible.

Dataset: https://github.com/ravyg/ate-agentic-coverage
Paper (Agentic Task Exposure): https://arxiv.org/abs/2604.00186

It's open under CC-BY-4.0, free to use with attribution. If it helps your research, a citation is the best thanks, and a star helps others find it.

If you'd like to help annotate the next validation round, fifteen minutes of your time gets your name in the acknowledgements. Reach out and I'll send you a batch.

More on my work: ravishgupta.me

#OpenData #ONET #LaborEconomics #FutureOfWork #AI #Automation
