
"""
MAZAISPraktiskaisDarbs

Eksperimenta fails domāts testēt SA algoritmu un tā struktūras
atkārtojamos testa piemēros.

Autors: je21033
"""

import argparse
import sys
import csv
import json

from typing import Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from time import perf_counter
from main import (
    SAConfig,
    Solution,
    build_initial_solution,
    generate_synthetic_data,
    simulated_annealing,
    d,
    Assignment
)


APP_NAME = "MAZAISPraktiskaisDarbs - Experiments"
VERSION = "0.0.1"

RESULTS_DIR = Path("results")
EXPERIMENT_RESULTS_DIR = RESULTS_DIR / "experiments"
BENCHMARK_RESULTS_DIR = RESULTS_DIR / "benchmarks"

REPETITIONS: int = 3

@dataclass(frozen=True)
class ExperimentConfig:
    """Configuration for one SA experiment."""
    name: str
    description: str
    n: int
    k: int
    sa_config: SAConfig
    instance_group: str


@dataclass(frozen=True)
class BenchmarkConfig:
    """Configuration for the best-known-solution benchmark."""
    name: str
    description: str
    method: str
    max_time_seconds: float = 300.0


@dataclass
class ExperimentResult:
    """SA experiment result."""
    config: ExperimentConfig
    initial_solution: Solution
    initial_cost: float
    final_solution: Solution
    final_cost: float
    elapsed_seconds: float
    result_valid: bool
    iterations: int
    temperature_levels: int
    stop_reason: str


@dataclass
class BenchmarkResult:
    """SA benchmark result."""
    method: str
    solution: Solution | None
    cost: float | None
    elapsed_seconds: float
    proven_optimal: bool
    stop_reason: str


# Default SA parameters are defined in SAConfig.
DEFAULT_SA_CONFIG = SAConfig()


# Experiment A: compare different problem sizes.
EXPERIMENT_A = {
    "small_default": ExperimentConfig(
        name="small_default",
        description="Small problem with default SA parameters.",
        n=10,
        k=3,
        sa_config=DEFAULT_SA_CONFIG,
        instance_group="small_default",
    ),
    "medium_default": ExperimentConfig(
        name="medium_default",
        description="Medium problem with default SA parameters.",
        n=100,
        k=10,
        sa_config=DEFAULT_SA_CONFIG,
        instance_group="medium_default",
    ),
    "large_default": ExperimentConfig(
        name="large_default",
        description="Large problem with default SA parameters.",
        n=500,
        k=25,
        sa_config=DEFAULT_SA_CONFIG,
        instance_group="large_default",
    ),
}


# Experiment B: compare cooling rates on the same problem size.
# All three configurations will later use the same generated instance.
EXPERIMENT_B = {
    "medium_cooling_090": ExperimentConfig(
        name="medium_cooling_090",
        description="Medium problem with cooling rate 0.90.",
        n=100,
        k=10,
        sa_config=SAConfig(cooling_rate=0.90),
        instance_group="medium_cooling_comparison",
    ),
    "medium_cooling_095": ExperimentConfig(
        name="medium_cooling_095",
        description="Medium problem with cooling rate 0.95.",
        n=100,
        k=10,
        sa_config=SAConfig(cooling_rate=0.95),
        instance_group="medium_cooling_comparison",
    ),
    "medium_cooling_099": ExperimentConfig(
        name="medium_cooling_099",
        description="Medium problem with cooling rate 0.99.",
        n=100,
        k=10,
        sa_config=SAConfig(cooling_rate=0.99),
        instance_group="medium_cooling_comparison",
    ),
}


# The benchmark is separate from the SA parameter experiments.
# It will later evaluate the same problem instance as the SA run.
BEST_KNOWN_CONFIG = BenchmarkConfig(
    name="best_known_solution",
    description="Independent benchmark for evaluating solution quality.",
    method="exhaustive_search",
)


# A single lookup table for command-line selection.
EXPERIMENTS = {
    **EXPERIMENT_A,
    **EXPERIMENT_B,
}


def print_experiment(config: ExperimentConfig) -> None:
    """Print an experiment's configuration."""
    print(f"\nExperiment: {config.name}")
    print(f"Description: {config.description}")
    print(f"People (N): {config.n}")
    print(f"Centers (K): {config.k}")
    print(f"Instance group: {config.instance_group}")
    print("SA parameters:")
    print(f"  Initial temperature: "
          f"{config.sa_config.initial_temperature}")
    print(f"  Cooling rate: {config.sa_config.cooling_rate}")
    print(f"  Iterations per temperature: "
          f"{config.sa_config.iterations_per_temperature}")
    print(f"  Minimum temperature: "
          f"{config.sa_config.minimum_temperature}")
    print(f"  Maximum neighbor attempts: "
          f"{config.sa_config.max_neighbor_attempts}")


def solution_to_dict(solution: Solution) -> dict:
    return {
        "cost": solution.cost(),
        "is_valid": solution.is_valid(),
        "hums": [
            {
                "id": str(hum.id),
                "location": {
                    "x": hum.location.x,
                    "y": hum.location.y,
                },
                "availability": {
                    "from_time": hum.available_time_window.from_time.isoformat(),
                    "to_time": hum.available_time_window.to_time.isoformat(),
                    "id": str(hum.available_time_window.id),
                },
            }
            for hum in solution.hums
        ],
        "vac_cens": [
            {
                "id": str(vac_cen.id),
                "location": {
                    "x": vac_cen.location.x,
                    "y": vac_cen.location.y,
                },
                "time_windows": [
                    {
                        "id": str(window.id),
                        "from_time": window.from_time.isoformat(),
                        "to_time": window.to_time.isoformat(),
                    }
                    for window in vac_cen.time_windows
                ],
            }
            for vac_cen in solution.vac_cens
        ],
        "assignments": [
            {
                "id": str(assignment.id),
                "hum_id": str(assignment.hum.id),
                "vac_cen_id": str(assignment.vac_cen.id),
                "time_window_id": str(assignment.time_window.id),
            }
            for assignment in solution.assignments
        ],
    }


def save_experiment_result(
    result: ExperimentResult,
    output_root: Path = EXPERIMENT_RESULTS_DIR,
) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir = output_root / f"{timestamp}_{result.config.name}"
    run_dir.mkdir()

    # Save experiment configuration.
    config_data = asdict(result.config)
    config_data["timestamp"] = timestamp

    with (run_dir / "config.json").open("w", encoding="utf-8") as file:
        json.dump(config_data, file, indent=2, ensure_ascii=False)

    # Save initial and final solution snapshots.
    with (run_dir / "initial_solution.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(
            solution_to_dict(result.initial_solution),
            file,
            indent=2,
            ensure_ascii=False,
        )

    with (run_dir / "final_solution.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(
            solution_to_dict(result.final_solution),
            file,
            indent=2,
            ensure_ascii=False,
        )

    # Calculate percentage cost reduction.
    improvement_percent = (
        (result.initial_cost - result.final_cost)
        / result.initial_cost
        * 100
        if result.initial_cost != 0
        else 0.0
    )

    # Save a human-readable summary.
    summary = (
        f"Experiment: {result.config.name}\n"
        f"Description: {result.config.description}\n"
        f"Timestamp: {timestamp}\n"
        f"N (people): {result.config.n}\n"
        f"K (centers): {result.config.k}\n"
        f"Initial cost: {result.initial_cost:.6f}\n"
        f"Final cost: {result.final_cost:.6f}\n"
        f"Cost reduction: {improvement_percent:.2f}%\n"
        f"Elapsed time: {result.elapsed_seconds:.6f} seconds\n"
        f"Iterations: {result.iterations}\n"
        f"Temperature levels: {result.temperature_levels}\n"
        f"Stop reason: {result.stop_reason}\n"
        f"Result valid: {result.result_valid}\n"
        f"SA configuration: {result.config.sa_config}\n"
    )

    with (run_dir / "summary.txt").open("w", encoding="utf-8") as file:
        file.write(summary)

    # Append one row to the shared comparison CSV.
    csv_path = output_root / "results.csv"
    csv_exists = csv_path.exists()

    row = {
        "timestamp": timestamp,
        "experiment_name": result.config.name,
        "instance_group": result.config.instance_group,
        "n": result.config.n,
        "k": result.config.k,
        "initial_cost": result.initial_cost,
        "final_cost": result.final_cost,
        "improvement_percent": improvement_percent,
        "elapsed_seconds": result.elapsed_seconds,
        "iterations": result.iterations,
        "result_valid": result.result_valid,
        "initial_temperature": result.config.sa_config.initial_temperature,
        "cooling_rate": result.config.sa_config.cooling_rate,
        "iterations_per_temperature":
            result.config.sa_config.iterations_per_temperature,
        "minimum_temperature": result.config.sa_config.minimum_temperature,
        "max_neighbor_attempts":
            result.config.sa_config.max_neighbor_attempts,
        "temperature_levels": result.temperature_levels,
        "stop_reason": result.stop_reason,
        "max_iterations": result.config.sa_config.max_iterations,
        "max_time_seconds": result.config.sa_config.max_time_seconds,
        "run_directory": str(run_dir),
    }

    with csv_path.open("a", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=row.keys())

        if not csv_exists:
            writer.writeheader()

        writer.writerow(row)

    return run_dir


def save_benchmark_result(
    benchmark: BenchmarkResult,
    initial_solution: Solution,
    sa_result: ExperimentResult,
    config: BenchmarkConfig,
) -> Path:
    output_root = BENCHMARK_RESULTS_DIR
    output_root.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir = output_root / f"{timestamp}_{config.name}"
    run_dir.mkdir()

    config_data = asdict(config)
    config_data["timestamp"] = timestamp

    with (run_dir / "config.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(config_data, file, indent=2, ensure_ascii=False)

    with (run_dir / "initial_solution.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(
            solution_to_dict(initial_solution),
            file,
            indent=2,
            ensure_ascii=False,
        )

    if benchmark.solution is not None:
        with (run_dir / "benchmark_solution.json").open(
            "w", encoding="utf-8"
        ) as file:
            json.dump(
                solution_to_dict(benchmark.solution),
                file,
                indent=2,
                ensure_ascii=False,
            )

    with (run_dir / "sa_solution.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(
            solution_to_dict(sa_result.final_solution),
            file,
            indent=2,
            ensure_ascii=False,
        )

    optimality_gap_percent = None

    if (
        benchmark.proven_optimal
        and benchmark.cost is not None
        and benchmark.cost > 0
    ):
        optimality_gap_percent = (
            (sa_result.final_cost - benchmark.cost)
            / benchmark.cost
            * 100
        )

    gap_text = (
        f"{optimality_gap_percent:.2f}%"
        if optimality_gap_percent is not None
        else "Unavailable (optimality not established or optimum is zero)"
    )

    summary = (
        f"Benchmark method: {benchmark.method}\n"
        f"Problem people: {len(initial_solution.hums)}\n"
        f"Problem centers: {len(initial_solution.vac_cens)}\n"
        f"Initial cost: {initial_solution.cost():.6f}\n"
        f"Benchmark cost: {benchmark.cost}\n"
        f"Benchmark elapsed: {benchmark.elapsed_seconds:.6f} seconds\n"
        f"Benchmark valid: "
        f"{benchmark.solution is not None and benchmark.solution.is_valid()}\n"
        f"Proven optimal: {benchmark.proven_optimal}\n"
        f"Benchmark stop reason: {benchmark.stop_reason}\n"
        f"SA cost: {sa_result.final_cost:.6f}\n"
        f"SA elapsed: {sa_result.elapsed_seconds:.6f} seconds\n"
        f"SA iterations: {sa_result.iterations}\n"
        f"SA stop reason: {sa_result.stop_reason}\n"
        f"SA valid: {sa_result.result_valid}\n"
        f"SA optimality gap: {gap_text}\n"
    )

    with (run_dir / "summary.txt").open(
        "w", encoding="utf-8"
    ) as file:
        file.write(summary)

    csv_path = output_root / "results.csv"
    csv_exists = csv_path.exists()

    row = {
        "timestamp": timestamp,
        "benchmark_method": benchmark.method,
        "n": len(initial_solution.hums),
        "k": len(initial_solution.vac_cens),
        "initial_cost": initial_solution.cost(),
        "benchmark_cost": benchmark.cost,
        "benchmark_elapsed_seconds": benchmark.elapsed_seconds,
        "benchmark_proven_optimal": benchmark.proven_optimal,
        "benchmark_stop_reason": benchmark.stop_reason,
        "sa_cost": sa_result.final_cost,
        "sa_elapsed_seconds": sa_result.elapsed_seconds,
        "sa_iterations": sa_result.iterations,
        "sa_stop_reason": sa_result.stop_reason,
        "optimality_gap_percent": optimality_gap_percent,
        "run_directory": str(run_dir),
    }

    with csv_path.open(
        "a", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=row.keys())

        if not csv_exists:
            writer.writeheader()

        writer.writerow(row)

    return run_dir


def save_experiment_averages(
    results: list[ExperimentResult],
    output_root: Path = EXPERIMENT_RESULTS_DIR,
) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    csv_path = output_root / "averages.csv"

    grouped: dict[str, list[ExperimentResult]] = {}

    for result in results:
        grouped.setdefault(result.config.name, []).append(result)

    rows = []

    for name, runs in grouped.items():
        count = len(runs)

        improvements = [
            (run.initial_cost - run.final_cost) / run.initial_cost * 100
            if run.initial_cost != 0
            else 0.0
            for run in runs
        ]

        rows.append({
            "experiment_name": name,
            "runs": count,
            "n": runs[0].config.n,
            "k": runs[0].config.k,
            "average_initial_cost": sum(r.initial_cost for r in runs) / count,
            "average_final_cost": sum(r.final_cost for r in runs) / count,
            "average_improvement_percent": sum(improvements) / count,
            "average_elapsed_seconds": sum(r.elapsed_seconds for r in runs) / count,
            "average_iterations": sum(r.iterations for r in runs) / count,
            "valid_runs": sum(r.result_valid for r in runs),
        })

    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    return csv_path


def save_benchmark_averages(
    results: list[tuple[BenchmarkResult, ExperimentResult]],
) -> Path:
    BENCHMARK_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = BENCHMARK_RESULTS_DIR / "averages.csv"

    benchmark_runs = [benchmark for benchmark, _ in results]
    sa_runs = [sa for _, sa in results]

    available_costs = [
        result.cost for result in benchmark_runs
        if result.cost is not None
    ]

    proven_runs = [
        benchmark for benchmark in benchmark_runs
        if benchmark.proven_optimal
    ]

    optimality_gaps = [
        (sa.final_cost - benchmark.cost) / benchmark.cost * 100
        for benchmark, sa in results
        if (
            benchmark.proven_optimal
            and benchmark.cost is not None
            and benchmark.cost > 0
        )
    ]

    count = len(results)

    row = {
        "runs": count,
        "n": len(results[0][1].initial_solution.hums),
        "k": len(results[0][1].initial_solution.vac_cens),
        "average_benchmark_cost": (
            sum(available_costs) / len(available_costs)
            if available_costs else None
        ),
        "runs_with_benchmark_solution": len(available_costs),
        "proven_optimal_runs": len(proven_runs),
        "average_benchmark_elapsed_seconds": (
            sum(r.elapsed_seconds for r in benchmark_runs) / count
        ),
        "average_sa_cost": sum(r.final_cost for r in sa_runs) / count,
        "average_sa_elapsed_seconds": (
            sum(r.elapsed_seconds for r in sa_runs) / count
        ),
        "average_sa_iterations": sum(r.iterations for r in sa_runs) / count,
        "average_optimality_gap_percent": (
            sum(optimality_gaps) / len(optimality_gaps)
            if optimality_gaps else None
        ),
    }

    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=row.keys())
        writer.writeheader()
        writer.writerow(row)

    return csv_path


def exhaustive_search(
    problem: Solution,
    deadline: float,
) -> tuple[Solution | None, bool]:
    hums = problem.hums
    vac_cens = problem.vac_cens

    # Find every center/slot combination that each person can use.
    eligible_slots = {}

    for hum in hums:
        candidates = []

        for vac_cen in vac_cens:
            if perf_counter() >= deadline:
                return None, False
            
            for window in vac_cen.time_windows:
                if perf_counter() >= deadline:
                    return None, False
                fits_availability = (
                    window.from_time >= hum.available_time_window.from_time
                    and window.to_time <= hum.available_time_window.to_time
                )

                if fits_availability:
                    candidates.append((vac_cen, window))

        if not candidates:
            raise ValueError(f"No eligible appointment slots for person {hum.id}.")

        # Try closer centers first to find a good solution early.
        candidates.sort(
            key=lambda candidate: d(
                hum.location,
                candidate[0].location,
            )
        )

        eligible_slots[hum.id] = candidates

    # Assign people with fewer choices first to reduce the search tree.
    ordered_hums = sorted(
        hums,
        key=lambda hum: len(eligible_slots[hum.id]),
    )

    best_solution = None
    best_cost = float("inf")
    assignments = []
    used_slot_ids = set()

    def search(index: int, current_cost: float) -> bool:
        nonlocal best_solution, best_cost

        if perf_counter() >= deadline:
            return False

        # All people have been assigned: evaluate this complete solution.
        if index == len(ordered_hums):
            candidate = Solution(
                hums=hums,
                vac_cens=vac_cens,
                assignments=list(assignments),
            )

            if candidate.is_valid() and current_cost < best_cost:
                best_solution = candidate
                best_cost = candidate.cost()

            return True

        hum = ordered_hums[index]

        for vac_cen, window in eligible_slots[hum.id]:
            if perf_counter() >= deadline:
                return False
            
            if window.id in used_slot_ids:
                continue

            distance = d(hum.location, vac_cen.location)

            # No need to explore a branch that cannot improve the best.
            if current_cost + distance >= best_cost:
                continue

            assignments.append(
                Assignment(
                    hum=hum,
                    vac_cen=vac_cen,
                    time_window=window,
                )
            )
            used_slot_ids.add(window.id)

            completed = search(index + 1, current_cost + distance)

            # Backtrack to explore the next possibility.
            used_slot_ids.remove(window.id)
            assignments.pop()
            
            if not completed:
                return False
        
        return True

    completed = search(0, 0.0)

    if not completed:
        return best_solution, False

    if best_solution is None:
        raise ValueError("No valid complete solution exists.")

    return best_solution, True


BENCHMARK_METHODS: dict[
    str,
    Callable[[Solution, float], tuple[Solution | None, bool]],
] = {
    "exhaustive_search": exhaustive_search,
}

def run_benchmark(
    problem: Solution,
    method_name: str,
    max_time_seconds: float = 300.0,
) -> BenchmarkResult:
    if max_time_seconds <= 0:
        raise ValueError("Benchmark time limit must be positive.")
    
    method = BENCHMARK_METHODS.get(method_name)

    if method is None:
        raise ValueError(f"Unknown benchmark method: {method_name}")

    start_time = perf_counter()
    deadline = start_time + max_time_seconds
    
    benchmark_solution, proven_optimal = method(problem, deadline)
    
    elapsed_seconds = perf_counter() - start_time

    if benchmark_solution is not None:
        if not benchmark_solution.is_valid():
            raise ValueError(
                f"Benchmark method '{method_name}' returned an invalid solution."
            )

        cost = benchmark_solution.cost()
    else:
        cost = None

    if proven_optimal:
        stop_reason = "completed"
    elif benchmark_solution is not None:
        stop_reason = "time_limit_with_solution"
    else:
        stop_reason = "time_limit_no_solution"

    return BenchmarkResult(
        method=method_name,
        solution=benchmark_solution,
        cost=cost,
        elapsed_seconds=elapsed_seconds,
        proven_optimal=proven_optimal,
        stop_reason=stop_reason,
    )


def run_experiment(
    config: ExperimentConfig,
    initial_solution: Solution | None = None,
) -> ExperimentResult:
    if initial_solution is None:
        # Generate a problem instance using this experiment's N and K.
        hums, vac_cens, assignments = generate_synthetic_data(
            n=config.n,
            k=config.k,
        )

        # Build and validate the initial solution.
        initial_solution = build_initial_solution(
            hums,
            vac_cens,
            assignments,
        )

    if not initial_solution.is_valid():
        raise ValueError(f"Initial solution for '{config.name}' is invalid.")

    initial_cost = initial_solution.cost()

    sa_result = simulated_annealing(
        initial_solution,
        config.sa_config,
    )

    # Validate and measure the resulting solution.
    final_solution = sa_result.best_solution
    result_valid = final_solution.is_valid()

    if not result_valid:
        raise ValueError(f"SA returned an invalid solution for '{config.name}'.")

    return ExperimentResult(
        config=config,
        initial_solution=initial_solution,
        initial_cost=initial_cost,
        final_solution=final_solution,
        final_cost=final_solution.cost(),
        elapsed_seconds=sa_result.elapsed_seconds,
        result_valid=result_valid,
        iterations=sa_result.iterations,
        temperature_levels=sa_result.temperature_levels,
        stop_reason=sa_result.stop_reason,
    )


def test_runner() -> None:
    result = run_experiment(EXPERIMENTS["small_default"])
    output_dir = save_experiment_result(result)

    print(f"Experiment: {result.config.name}")
    print(f"Initial cost: {result.initial_cost:.4f}")
    print(f"Final cost: {result.final_cost:.4f}")
    print(f"Elapsed time: {result.elapsed_seconds:.4f} seconds")
    print(f"Iterations: {result.iterations}")
    print(f"Temperature levels: {result.temperature_levels}")
    print(f"Stop reason: {result.stop_reason}")
    print(f"Valid result: {result.result_valid}")
    print(f"Saved to: {output_dir}")


def test_benchmark() -> None:
    # Initial cost: ~187.6570
    # Benchmark cost: ~187.6570
    # Elapsed time: ~0.001451 seconds
    # hums, vac_cens, assignments = generate_synthetic_data(n=3, k=1)
    # Initial cost: ~199.1584
    # Benchmark cost: ~161.8479
    # Elapsed time: ~0.005987 seconds
    # hums, vac_cens, assignments = generate_synthetic_data(n=3, k=2)
    # Initial cost: ~435.8708
    # Benchmark cost: ~166.8049
    # Elapsed time: ~300.000006 seconds
    hums, vac_cens, assignments = generate_synthetic_data(n=10, k=5)

    initial_solution = build_initial_solution(
        hums,
        vac_cens,
        assignments,
    )

    benchmark = run_benchmark(
        initial_solution,
        BEST_KNOWN_CONFIG.method,
        # max_time_seconds=10.0,  # Short test limit.
    )

    print(f"Method: {benchmark.method}")
    print(f"Initial cost: {initial_solution.cost()}")
    print(f"Benchmark cost: {benchmark.cost}")
    print(f"Elapsed time: {benchmark.elapsed_seconds:.6f} seconds")
    print(
        "Valid:",
        benchmark.solution is not None
        and benchmark.solution.is_valid(),
    )
    print(f"Proven optimal: {benchmark.proven_optimal}")
    print(f"Stop reason: {benchmark.stop_reason}")


def run_experiment_suite() -> None:
    print("\n=== Experiment suite ===")

    all_results: list[ExperimentResult] = []

    # Experiment A: repeat each problem size on independent instances.
    for name in (
        "small_default",
        "medium_default",
        "large_default",
    ):
        config = EXPERIMENTS[name]

        print(f"\nRunning {name}: N={config.n}, K={config.k}")

        for repetition in range(1, REPETITIONS + 1):
            print(f"  Repetition {repetition}/{REPETITIONS}")

            result = run_experiment(config)
            all_results.append(result)

            output_dir = save_experiment_result(result)

            print(f"  Initial cost: {result.initial_cost:.4f}")
            print(f"  Final cost: {result.final_cost:.4f}")
            print(f"  Elapsed: {result.elapsed_seconds:.4f} seconds")
            print(f"  Saved to: {output_dir}")

    # Experiment B: compare cooling rates on the same instance
    # within each repetition.
    cooling_names = (
        "medium_cooling_090",
        "medium_cooling_095",
        "medium_cooling_099",
    )

    first_config = EXPERIMENTS[cooling_names[0]]

    for repetition in range(1, REPETITIONS + 1):
        hums, vac_cens, assignments = generate_synthetic_data(
            n=first_config.n,
            k=first_config.k,
        )

        shared_initial_solution = build_initial_solution(
            hums, vac_cens, assignments
        )

        print(
            f"\nCooling comparison repetition "
            f"{repetition}/{REPETITIONS}"
        )

        for name in cooling_names:
            config = EXPERIMENTS[name]

            result = run_experiment(
                config,
                initial_solution=shared_initial_solution,
            )
            all_results.append(result)

            output_dir = save_experiment_result(result)

            print(
                f"  {name}: final cost={result.final_cost:.4f}, "
                f"time={result.elapsed_seconds:.4f}s"
            )
            print(f"  Saved to: {output_dir}")

    averages_path = save_experiment_averages(all_results)
    print(f"\nExperiment averages saved to: {averages_path}")


def run_benchmark_suite() -> None:
    print("\n=== Benchmark suite ===")

    n = 10
    k = 3
    all_results: list[tuple[BenchmarkResult, ExperimentResult]] = []

    sa_config = ExperimentConfig(
        name="benchmark_sa_comparison",
        description="SA comparison against the benchmark on the same instance.",
        n=n,
        k=k,
        sa_config=DEFAULT_SA_CONFIG,
        instance_group="benchmark",
    )

    for repetition in range(1, REPETITIONS + 1):
        print(f"\nBenchmark repetition {repetition}/{REPETITIONS}")

        hums, vac_cens, assignments = generate_synthetic_data(n=n, k=k)
        initial_solution = build_initial_solution(
            hums, vac_cens, assignments
        )

        benchmark = run_benchmark(
            initial_solution,
            BEST_KNOWN_CONFIG.method,
            max_time_seconds=BEST_KNOWN_CONFIG.max_time_seconds,
        )

        # Compare SA against the benchmark on this exact same instance.
        sa_result = run_experiment(
            sa_config,
            initial_solution=initial_solution,
        )

        all_results.append((benchmark, sa_result))

        output_dir = save_benchmark_result(
            benchmark=benchmark,
            initial_solution=initial_solution,
            sa_result=sa_result,
            config=BEST_KNOWN_CONFIG,
        )

        print(f"Benchmark cost: {benchmark.cost}")
        print(f"Proven optimal: {benchmark.proven_optimal}")
        print(f"SA cost: {sa_result.final_cost:.4f}")
        print(f"Saved to: {output_dir}")

    averages_path = save_benchmark_averages(all_results)
    print(f"\nBenchmark averages saved to: {averages_path}")


def run_all_tests() -> None:
    """Run the complete experiment suite, then the benchmark suite."""
    print("Starting complete test suite.")

    run_experiment_suite()
    run_benchmark_suite()

    print("\nComplete test suite finished.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=APP_NAME,
    )

    parser.add_argument(
        "suite",
        nargs="?",
        choices=[
            "all",
            "experiments",
            "benchmarks",
            *EXPERIMENTS.keys(),
            BEST_KNOWN_CONFIG.name,
        ],
        default="all",
        help="Which experiment or suite to run.",
    )

    args = parser.parse_args(argv)

    if args.suite == "all":
        run_all_tests()

    elif args.suite == "experiments":
        run_experiment_suite()

    elif args.suite in ("benchmarks", BEST_KNOWN_CONFIG.name):
        run_benchmark_suite()

    else:
        config = EXPERIMENTS[args.suite]
        result = run_experiment(config)
        output_dir = save_experiment_result(result)

        print(f"Experiment: {config.name}")
        print(f"Initial cost: {result.initial_cost:.4f}")
        print(f"Final cost: {result.final_cost:.4f}")
        print(f"Iterations: {result.iterations}")
        print(f"Elapsed: {result.elapsed_seconds:.4f} seconds")
        print(f"Stop reason: {result.stop_reason}")
        print(f"Valid: {result.result_valid}")
        print(f"Saved to: {output_dir}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
        # test_runner()
        # test_benchmark()
    except ValueError as val_err:
        print(f"Configuration error: {val_err}", file=sys.stderr)
        sys.exit(1)
