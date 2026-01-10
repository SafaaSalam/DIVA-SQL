# DIVA-SQL Benchmark Evaluation

This directory contains scripts for evaluating DIVA-SQL on established Text-to-SQL benchmarks.

## Overview

The evaluation system tests DIVA-SQL on two major benchmarks:

1. **Spider**: A complex and cross-domain semantic parsing and text-to-SQL dataset
2. **BIRD**: A big bench for large-scale database grounded text-to-SQL

## Getting Started

### Prerequisites

- Python 3.7+
- Required packages: pandas, matplotlib, seaborn, tqdm
- Google API key for Gemini access
- At least 1GB free disk space for datasets

### Installation

1. Set up your Google API key:

```bash
export GOOGLE_API_KEY='your_api_key_here'
```

2. Install required packages:

```bash
pip install pandas matplotlib seaborn tqdm
```

## Running the Benchmark

### Quick Start

For a simple test run, execute:

```bash
./run_benchmark.sh
```

This will:
1. Download the benchmark datasets
2. Run a small sample evaluation on each benchmark
3. Generate analysis and visualizations

### Manual Execution

#### 1. Download Datasets

```bash
python evaluation/download_datasets.py
```

#### 2. Run Rate-Limited Evaluation

```bash
python evaluation/rate_limited_eval.py --benchmark spider --sample 10 --delay 3
```

Options:
- `--benchmark`: Choose 'spider' or 'bird'
- `--sample`: Number of queries to sample
- `--delay`: Seconds between API calls (to avoid rate limits)
- `--model`: LLM model to use (default: gemini-2.0-flash)
- `--output`: Results output file

#### 3. Analyze Results

```bash
python evaluation/analyze_results.py --results results/spider_results.csv
```

This will generate visualizations and a summary JSON in the results directory.

## Understanding the Results

The evaluation provides several metrics:

- **Execution Accuracy**: Percentage of queries where DIVA-SQL produces SQL that returns the same results as the gold standard SQL
- **Syntactic Validity**: Percentage of queries where DIVA-SQL produces syntactically valid SQL
- **Success Rate**: Percentage of queries where DIVA-SQL completes without errors
- **Confidence Score**: System's self-reported confidence in the generated SQL
- **Semantic Node Count**: Number of decomposition steps used by DIVA-SQL

## Visualizations

The analysis generates several visualizations:

1. **Status Distribution**: Overall success rates
2. **Confidence Distribution**: Histogram of confidence scores
3. **Confidence vs. Correctness**: Relationship between confidence and accuracy
4. **Node Distribution**: Distribution of semantic decomposition complexity
5. **Time vs. Complexity**: Execution time relative to query complexity
6. **Accuracy by Complexity**: How accuracy varies with query complexity

## Citation

When using these benchmarks for academic purposes, please cite the original datasets:

- **Spider**:
  ```
  @inproceedings{yu2018spider,
    title={Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task},
    author={Yu, Tao and Zhang, Rui and Yang, Kai and Yasunaga, Michihiro and Wang, Dongxu and Li, Zifan and Ma, James and Li, Irene and Yao, Qingning and Roman, Shanelle and others},
    booktitle={Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing},
    pages={3911--3921},
    year={2018}
  }
  ```

- **BIRD**:
  ```
  @inproceedings{li2023can,
    title={Can LLM Already Serve as A Database Interface? A BIg Bench for Large-Scale Database Grounded Text-to-SQL},
    author={Li, Jinyang and Hui, Binyuan and Qu, Ge and Yang, Jiaxi and Li, Binhua and Li, Bo and Qin, Bowen and Shi, Tianxiang and Xu, Ruiying and Zhang, Yongbin and others},
    booktitle={Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics},
    year={2023}
  }
  ```
