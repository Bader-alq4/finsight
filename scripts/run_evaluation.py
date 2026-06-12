import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.evaluation.runner import run_evaluation

if __name__ == "__main__":
    run_evaluation(csv_path="data/finsight_eval.csv")