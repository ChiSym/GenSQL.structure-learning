from inferenceql_auto_modeling.cgpm import CGPMModel
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="")

    parser.add_argument(
        "metadata",
        type=str,
        help="CGPM metadata JSON",
        default=sys.stdin,
        metavar="PATH",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=sys.stdout,
        metavar="PATH",
    )
    parser.add_argument(
        "-k",
        "--kernel",
        action="append",
        type=str,
        help="Inference kernel.",
        default=["alpha", "view_alphas", "column_hypers"],
        metavar="KERNEL",
        dest="kernels",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        help="Number of inference iterations",
        default=None,
        metavar="NUM",
    )
    parser.add_argument(
        "--minutes",
        type=float,
        help="Minutes inference should run.",
        default=None,
        metavar="NUM",
    )
    parser.add_argument("--seed", type=int, default=1, help="CGPM seed.")

    args = parser.parse_args()

    if args.metadata is None:
        parser.print_help(sys.stderr)
        raise TypeError("Metadata needs to be passed as an argument.")

    cgpm = CGPMModel.from_metadata(args.metadata, args.seed)

    S = None if args.minutes is None else args.minutes * 60
    cgpm.inference(N=args.iterations, S=S, kernels=args.kernels)
    cgpm.to_metadata(args.output)


if __name__ == "__main__":
    main()
