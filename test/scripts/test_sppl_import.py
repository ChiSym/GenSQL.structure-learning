import edn_format
from edn_format import Keyword
import sppl
import sys

# XXX: this is not how this should be done.
sys.path.insert(0, "scripts")
from sppl_import import convert_primitive
from sppl_import import convert_cluster
from sppl_import import convert_view


primitive_dist_categorical = {
    Keyword("distribution/type"): Keyword("distribution.type/categorical"),
    Keyword("categorical/category->weight"): {
        "category a": 0.2,
        "category b": 0.3,
        "category c": 0.5,
    },
}

primitive_dist_student_t = {
    Keyword("distribution/type"): Keyword("distribution.type/student-t"),
    Keyword("student-t/degrees-of-freedom"): 2,
    Keyword("student-t/location"): 1.0,
    Keyword("student-t/scale"): 3,
}


primitive_dist_negative_binom = {
    Keyword("distribution/type"): Keyword("distribution.type/negative-binom"),
    Keyword("negative-binom/n"): 2,
    Keyword("negative-binom/p"): 0.5,
}


def test_convert_primitive_categorical():
    leaf = convert_primitive("column_foo", primitive_dist_categorical)
    assert isinstance(leaf, sppl.spe.NominalLeaf)


def test_convert_primitive_student_t():
    leaf = convert_primitive("column_bar", primitive_dist_student_t)
    assert isinstance(leaf, sppl.spe.ContinuousLeaf)


def test_convert_primitive_negative_binom():
    leaf = convert_primitive("column_baz", primitive_dist_negative_binom)
    assert isinstance(leaf, sppl.spe.DiscreteLeaf)


def test_convert_cluster():
    cluster = {
        "column_foo": primitive_dist_categorical,
        "column_bar": primitive_dist_student_t,
    }
    cluster_product_node = convert_cluster(0, 0, cluster)
    assert isinstance(cluster_product_node, sppl.spe.ProductSPE)


def test_convert_view():
    view = [
        {
            Keyword("cluster/weight"): 0.6,
            Keyword("cluster/column->distribution"): {
                "foo": primitive_dist_categorical,
                "bar": primitive_dist_student_t,
            },
        },
        {
            Keyword("cluster/weight"): 0.4,
            Keyword("cluster/column->distribution"): {
                "foo": primitive_dist_categorical,
                "bar": primitive_dist_student_t,
            },
        },
    ]
    view_sum_node = convert_view(0, view)
    assert isinstance(view_sum_node, sppl.spe.SumSPE)
