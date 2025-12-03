
import pandas as pd
import random
from multiprocessing import Pool, cpu_count
from typing import Callable, List, Dict, Any, Optional

# Global variable to hold the DataFrame in worker processes
_GLOBAL_DF: Optional[pd.DataFrame] = None

def init_worker(df: pd.DataFrame) -> None:
    """
    Initializer for worker processes. Sets the global DataFrame.
    """
    global _GLOBAL_DF
    _GLOBAL_DF = df

def get_global_df() -> pd.DataFrame:
    """
    Retrieve the global DataFrame in a worker process.
    """
    if _GLOBAL_DF is None:
        raise RuntimeError("Global DataFrame not initialized in worker process.")
    return _GLOBAL_DF

def run_optimization(
    evaluator_func: Callable[[Any], Optional[Dict[str, Any]]],
    param_grid: List[Any],
    df: pd.DataFrame,
    max_combos: int = 2000,
    n_jobs: Optional[int] = None,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Runs the optimization process.

    Args:
        evaluator_func: Function that takes a config tuple/object and returns a result dict or None.
        param_grid: List of configuration tuples/objects to evaluate.
        df: The DataFrame to use for backtesting.
        max_combos: Maximum number of combinations to test. If len(param_grid) > max_combos, it samples.
        n_jobs: Number of processes to use. Defaults to cpu_count() - 1.
        seed: Random seed for sampling.

    Returns:
        List of result dictionaries.
    """
    total_full = len(param_grid)
    print(f"Total combinations generated: {total_full}")

    if total_full > max_combos:
        print(f"Reducing to {max_combos} random samples...")
        random.seed(seed)
        param_grid = random.sample(param_grid, max_combos)

    total_combos = len(param_grid)
    
    if n_jobs is None:
        n_jobs = max(1, cpu_count() - 1)
    
    print(f"Using {n_jobs} processes.")

    rows: List[Dict[str, Any]] = []
    progress_step = max(1, total_combos // 20)

    with Pool(processes=n_jobs, initializer=init_worker, initargs=(df,)) as pool:
        for idx, res in enumerate(
            pool.imap_unordered(evaluator_func, param_grid, chunksize=10),
            start=1,
        ):
            if res is not None:
                rows.append(res)

            if idx % progress_step == 0 or idx == total_combos:
                pct = idx / total_combos * 100.0
                print(f"Progress: {idx}/{total_combos} ({pct:.1f}%) - valid: {len(rows)}", flush=True)

    return rows

def save_results(
    results: List[Dict[str, Any]],
    symbol: str,
    timeframe: str,
    strategy_name: str,
    top_n: int = 20
) -> None:
    """
    Sorts, prints top N, and saves results to CSV.
    """
    if not results:
        print(f"{strategy_name}: No valid results found.")
        return

    df_results = pd.DataFrame(results)
    
    # Ensure columns exist before sorting
    sort_cols = ["total_return_pct", "profit_factor", "max_drawdown_pct"]
    ascending = [False, False, True]
    
    # Filter out columns that might not exist (though they should)
    actual_sort_cols = [c for c in sort_cols if c in df_results.columns]
    actual_ascending = [ascending[i] for i, c in enumerate(sort_cols) if c in df_results.columns]

    if actual_sort_cols:
        df_results = df_results.sort_values(
            by=actual_sort_cols,
            ascending=actual_ascending,
        ).reset_index(drop=True)

    print(f"\nTop {top_n} {strategy_name} {symbol} {timeframe}:")
    print(df_results.head(top_n))

    safe_symbol = symbol.replace("/", "")
    out_path = f"opt_{strategy_name.lower()}_{safe_symbol}_{timeframe}.csv"
    df_results.to_csv(out_path, index=False)
    print(f"\nResults saved to {out_path}")
