import json
import math
import numpy as np

from cgpm.crosscat.state import State
from cgpm.utils import general as gu

from cgpm_infer import replace


class Streamcat:
    """CGpm Crosscat plus handy metadata and metafunction for streaming
    inference."""

    def __init__(self, X, col_names, incorporated, incorporated_rows, seed, **kwargs):
        self.col_names = col_names
        self.outputs = range(len(col_names))
        self.incorporated_cols = incorporated
        self.incorporated_rows = incorporated_rows
        self.distargs = kwargs.get("distargs_orig_order", None)
        self.cctypes = kwargs.get("cctypes_orig_order", None)
        self.X = X
        self.T = X.shape[0]
        self.counter = 0
        # TODO: add switch for  checkpointing.
        # Initialize a CGPM-CrossCat state with a subset of rows and cols.
        init_state_args = kwargs
        init_X = X[:1, [col_names.index(c) for c in incorporated]]
        init_outputs = list(range(len(incorporated)))
        init_distargs = [self.distargs[col_names.index(c)] for c in incorporated]
        init_cctypes = [self.cctypes[col_names.index(c)] for c in incorporated]
        # Track the seed to save checkpoints.
        self.seed = seed
        self.rng = gu.gen_rng(seed)
        self.state = State(
            init_X,
            outputs=init_outputs,
            distargs=init_distargs,
            cctypes=init_cctypes,
            rng=self.rng,
        )

    @classmethod
    def from_metadata(cls, metadata, rng=None):
        # XXX: Copy pasta from CGPM.state"""
        if rng is None:
            rng = gu.gen_rng(0)
        to_dict = lambda val: None if val is None else dict(val)
        # Build the State.
        state = cls(
            np.asarray(metadata["X"]),
            metadata["col_names"],
            metadata["incorporated_cols"],
            metadata["incorporated_rows"],
            metadata["seed"],
            outputs=metadata.get("outputs", None),
            cctypes_orig_order=metadata.get("cctypes_orig_order", None),
            distargs_orig_order=metadata.get("distargs_orig_order", None),
            alpha=metadata.get("alpha", None),
            Zv=to_dict(metadata.get("Zv", None)),
            Zrv=to_dict(metadata.get("Zrv", None)),
            view_alphas=to_dict(metadata.get("view_alphas", None)),
            hypers=metadata.get("hypers", None),
            Cd=metadata.get("Cd", None),
            Ci=metadata.get("Ci", None),
            diagnostics=metadata.get("diagnostics", None),
            loom_path=metadata.get("loom_path", None),
            rng=rng,
        )
        return state

    def to_metadata(self):
        metadata = self.state.to_metadata()
        metadata["col_names"] = self.col_names
        metadata["distargs_orig_order"] = self.distargs
        metadata["cctypes_orig_order"] = self.cctypes
        metadata["incorporated_cols"] = self.incorporated_cols
        metadata["incorporated_rows"] = self.incorporated_rows
        metadata["seed"] = self.seed
        return metadata

    def safe_incorporate_row(self, t):
        """Safely incorporate a partial row.
        "Partial" refers to all already incorporated columns in row index t.

        We use t as row index because of SMC conventions.

        For SMC, this will need to return a weight (currently stubbed)."""
        self.state.incorporate(
            t,
            {
                self.incorporated_cols.index(col_name): self.X[
                    t, self.col_names.index(col_name)
                ]
                for col_name in self.incorporated_cols
                if ~np.isnan(self.X[t, self.col_names.index(col_name)])
            },
        )
        self.incorporated_rows += 1
        # This is a stub. For SMC, we need to return a real weight here.
        return 0.0

    def safe_incorporate_col(self, col_name):
        """Safely incorporate a partial column.
        "Partial" refers to all already incorporated rows.

        For SMC, this will need to return a weight (currently stubbed)."""
        state_cid = len(self.incorporated_cols)
        stream_cid = self.col_names.index(col_name)
        col_data = self.X[0 : self.incorporated_rows, stream_cid]
        if np.all(np.isnan(col_data)):
            return None
        else:
            self.state.incorporate_dim(
                col_data.tolist(),
                [state_cid],
                cctype=self.cctypes[stream_cid],
                distargs=self.distargs[stream_cid],
            )
            self.incorporated_cols.append(col_name)
            # This is a stub. For SMC, we need to return a real weight here.
            return 0.0

    def transition_rows(self, rows=None):
        self.state.transition_view_rows(rows=rows)
        self.state.transition_view_alphas()
        self.state.transition_dim_hypers()
        self.save_checkpoint()

    def transition_cols(self, cols=None):
        if cols is None:
            cols = self.incorporated_cols
        col_ids = [cid for cid, col_name in enumerate(cols)]
        self.rng.shuffle(col_ids)
        for col_id in col_ids:
            self.state.transition_dims(col_id)
            self.save_checkpoint()
        self.state.transition_crp_alpha()  # Do I need this here?

    def transition_hypers(self):
        self.state.transition_crp_alpha()
        self.state.transition_view_alphas()
        self.state.transition_dim_hypers()

    def insert_rows(self, rows):
        for row in rows:
            self.safe_incorporate_row(row)
            self.transition_rows([row])

    def insert_cols(self, cols):
        for col in cols:
            weigth = self.safe_incorporate_col(col)
            if weigth is not None:
                self.transition_cols([cols])

    def other_cols(self):
        return [c for c in self.col_names if c not in self.incorporated_cols]

    def random_other_col(self):
        return self.rng.choice(self.other_cols())

    def save_checkpoint(self):
        metadata = self.state.to_metadata()
        n, d = self.X.shape
        metadata["n"] = n
        metadata["d"] = d
        metadata["col_names"] = self.incorporated_cols
        json.dump(
            metadata,
            open(
                "data/cgpm/checkpoints/sample-{}/t-{}.json".format(
                    self.seed, str(self.counter).zfill(8)
                ),
                "w",
            ),
        )
        self.counter += 1
