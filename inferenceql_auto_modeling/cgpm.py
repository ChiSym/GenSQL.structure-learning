from cgpm.crosscat.state import State
from inferenceql_auto_modeling.utils import distarg, replace, _proportion_done
from inferenceql_auto_modeling.slice_sampling import (
    kernel_alpha,
    kernel_view_alphas,
    kernel_column_hypers,
)
import cgpm.utils.general as general
import numpy as np
import math
import time
import json


class CGPMModel:
    def __init__(self, cgpm, model_type, columns_to_not_transition=[]):
        self.cgpm = cgpm
        self.model_type = model_type
        self.columns_to_not_transition = columns_to_not_transition
        self.columns_to_transition = [
            i for i in range(len(cgpm.outputs)) if i not in columns_to_not_transition
        ]

    @classmethod
    def from_data(
        cls,
        df,
        schema,
        mapping_table,
        seed=0,
        model="CrossCat",
        cgpm_params={},
        additional_metadata={},
    ):
        if "hooked_cgpms" not in additional_metadata.keys():
            additional_metadata["hooked_cgpms"] = {}

        cctypes = [schema[column] for column in df.columns]
        distargs = [distarg(column, mapping_table, schema) for column in df.columns]
        column_mapping = {c: i for i, c in enumerate(df.columns)}

        base_metadata = dict(
            X=df.values, cctypes=cctypes, distargs=distargs, outputs=range(df.shape[1])
        )

        match model:
            case "CrossCat":
                do_not_transition = []
                # We can't transition columns that are constrained to be dependent.
                if "dependence" in cgpm_params:
                    for target_column, columns_to_move in cgpm_params[
                        "dependence"
                    ].items():
                        for column_to_move in columns_to_move:
                            if "Zv" in additional_metadata.keys():
                                Zv = additional_metadata["Zv"]
                                if (
                                    Zv[column_mapping[column_to_move]]
                                    != Zv[column_mapping[target_column]]
                                ):
                                    raise TypeError(
                                        "Can't initialize a dependence-constrained model from a different model that doesn't satisfy those dependencies"
                                    )
                            do_not_transition.append(column_mapping[column_to_move])
                        do_not_transition.append(column_mapping[target_column])
                # Independence is solved using CGPM's independence constraints.
                if "independence" in cgpm_params:
                    Ci = []
                    for c1, cols in cgpm_params["independence"].items():
                        for c2 in cols:
                            Ci.append(tuple([column_mapping[c1], column_mapping[c2]]))
                    base_metadata["Ci"] = Ci
            case "DPMM":
                base_metadata["Zv"] = {i: 0 for i in range(len(cctypes))}
                do_not_transition = [i for i in range(df.shape[1])]
            case "Independent":
                base_metadata["Zv"] = {i: i for i in range(len(cctypes))}
                cluster_idx = [0] * df.shape[0]
                base_metadata["Zrv"] = {i: cluster_idx for i in range(df.shape[1])}
                do_not_transition = [i for i in range(df.shape[1])]
            case _:
                raise ValueError(f"Model '{model}' not defined")

        metadata = {**base_metadata, **additional_metadata}
        rng = general.gen_rng(seed)

        cgpm = State.from_metadata(metadata, rng=rng)

        model_type = model
        columns_to_not_transition = do_not_transition

        return cls(
            cgpm, model_type, columns_to_not_transition=columns_to_not_transition
        )

    @classmethod
    def from_metadata(cls, path, seed=0):
        metadata = json.load(open(path, "r", encoding="utf8"))
        metadata["X"] = replace(metadata["X"], lambda x: x is None, math.nan)

        cgpm = State.from_metadata(metadata, rng=general.gen_rng(seed))
        model_type = metadata["model_type"]
        columns_to_not_transition = metadata["columns_to_not_transition"]

        return cls(
            cgpm,
            model_type,
            columns_to_not_transition=columns_to_not_transition,
        )

    def to_metadata(self, path):
        cgpm_metadata = self.cgpm.to_metadata()
        cgpm_metadata["X"] = replace(cgpm_metadata["X"], math.isnan, None)
        cgpm_metadata["model_type"] = self.model_type
        cgpm_metadata["columns_to_not_transition"] = self.columns_to_not_transition
        cgpm_metadata["columns_to_transition"] = self.columns_to_transition

        json.dump(cgpm_metadata, open(path, "w", encoding="utf8"))

    def kernel_lookup(self, kernel):
        match kernel:
            case "alpha":
                kernel_alpha(self.cgpm)
            case "view_alphas":
                kernel_view_alphas(self.cgpm)
            case "column_hypers":
                kernel_column_hypers(self.cgpm)
            case "rows":
                self.cgpm.transition_view_rows()
            case "columns":
                self.cgpm.transition_dims(cols=self.columns_to_transition)
            case _:
                raise NotImplementedError("kernel not found")

    def inference(
        self,
        N=None,
        S=None,
        kernels=["alpha", "view_alphas", "column_hypers", "rows", "columns"],
        progress=True,
        checkpoint=None,
    ):
        iters = 0
        start = time.time()

        if self.model_type in ["DPMM", "Independent"]:
            kernels = [k for k in kernels if k not in ["alpha", "columns"]]

        while True and kernels:
            for kernel in kernels:
                p = _proportion_done(N, S, iters, start)
                if progress:
                    self.cgpm._progress(p)
                if p >= 1.0:
                    break
                self.kernel_lookup(kernel)
            else:
                iters += 1
                if checkpoint and (iters % checkpoint == 0):
                    self.cgpm._increment_diagnostics()
                continue
            break

        if progress:
            print(
                "\rCompleted: %d iterations in %f minutes."
                % (iters, (time.time() - start) / 60)
            )
