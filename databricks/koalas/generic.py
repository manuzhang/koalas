#
# Copyright (C) 2019 Databricks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
A base class to be monkey-patched to DataFrame/Column to behave similar to pandas DataFrame/Series.
"""
import pandas as pd
from pyspark.sql import Column, DataFrame, functions as F

from databricks.koalas.dask.utils import derived_from

max_display_count = 1000


class _Frame(object):
    """
    The base class for both dataframes and series.
    """

    @derived_from(pd.DataFrame, ua_args=['axis', 'skipna', 'level', 'numeric_only'])
    def mean(self):
        return self._reduce_for_stat_function(F.mean)

    @derived_from(pd.DataFrame, ua_args=['axis', 'skipna', 'level', 'numeric_only', 'min_count'])
    def sum(self):
        return self._reduce_for_stat_function(F.sum)

    @derived_from(pd.DataFrame, ua_args=['axis', 'skipna', 'level', 'numeric_only'])
    def skew(self):
        return self._reduce_for_stat_function(F.skewness)

    @derived_from(pd.DataFrame, ua_args=['axis', 'skipna', 'level', 'numeric_only'])
    def kurtosis(self):
        return self._reduce_for_stat_function(F.kurtosis)

    kurt = kurtosis

    @derived_from(pd.DataFrame, ua_args=['axis', 'skipna', 'level', 'numeric_only'])
    def min(self):
        return self._reduce_for_stat_function(F.min)

    @derived_from(pd.DataFrame, ua_args=['axis', 'skipna', 'level', 'numeric_only'])
    def max(self):
        return self._reduce_for_stat_function(F.max)

    @derived_from(pd.DataFrame, ua_args=['axis', 'skipna', 'level', 'ddof', 'numeric_only'])
    def std(self):
        return self._reduce_for_stat_function(F.stddev)

    @derived_from(pd.DataFrame, ua_args=['axis', 'skipna', 'level', 'ddof', 'numeric_only'])
    def var(self):
        return self._reduce_for_stat_function(F.variance)

    @derived_from(pd.DataFrame)
    def abs(self):
        """
        Return a Series/DataFrame with absolute numeric value of each element.

        :return: :class:`Series` or :class:`DataFrame` with the absolute value of each element.
        """
        return _spark_col_apply(self, F.abs)

    def compute(self):
        """Alias of `toPandas()` to mimic dask for easily porting tests."""
        return self.toPandas()


def _spark_col_apply(col_or_df, sfun):
    """
    Performs a function to all cells on a dataframe, the function being a known sql function.
    """
    if isinstance(col_or_df, Column):
        return sfun(col_or_df)
    assert isinstance(col_or_df, DataFrame)
    df = col_or_df
    df = df._spark_select([sfun(df[col]).alias(col) for col in df.columns])
    return df


def anchor_wrap(df, col):
    """
    Ensures that the column has an anchoring reference to the dataframe.

    This is required to get self-representable columns.
    :param df: dataframe or column
    :param col: a column
    :return: column
    """
    if isinstance(col, Column):
        if isinstance(df, Column):
            ref = df._pandas_anchor
        else:
            assert isinstance(df, DataFrame), type(df)
            ref = df
        col._spark_ref_dataframe = ref
    return col
