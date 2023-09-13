from inferenceql_auto_modeling.cgpm import CGPMModel


def test_slice_sampling_changes_parameters():
    metadata_path = "test/satellites/hydrated_sample.0.json"
    wrapper = CGPMModel.from_metadata(metadata_path)
    wrapper.cgpm.transition_dim_hypers()

    state = wrapper.cgpm
    prev_alpha = state.crp.hypers["alpha"]

    wrapper.inference(N=100, kernels=["alpha", "view_alphas", "column_hypers"])

    assert prev_alpha != state.crp.hypers["alpha"]
