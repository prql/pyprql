# -*- coding: utf-8 -*-
import sqlite3
import unittest
from pathlib import Path

from pyprql.lang import prql


class TestEmployeeExamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Use Path for robust construction, but sqlite3 py3.6 requires str
        db_path = str(Path("tests", "../resources/employee.db"))
        cls.con = sqlite3.connect(db_path)  # type:ignore[attr-defined]
        cls.cur = cls.con.cursor()  # type:ignore[attr-defined]

    def run_query(self, text, expected=None):
        print(text.replace("\n\n", "\n"))
        print("-" * 40)
        sql = prql.to_sql(text)
        print(sql)
        rows = self.cur.execute(sql)
        columns = [d[0] for d in rows.description]
        print(f"Columns: {columns}")
        rows = rows.fetchall()
        if expected is not None:
            assert len(rows) == expected

    def test_index(self):
        text = """
        from employees
        filter country = "USA"                           # Each line transforms the previous result.
        derive [                                         # This adds columns / variables.
          gross_salary: salary + payroll_tax,
          gross_cost:   gross_salary + benefits_cost     # Variables can use other variables.
        ]
        filter gross_cost > 0
        aggregate by:[title, country] [                  # `by` are the columns to group by.
            average salary,                              # These are aggregation calcs run on each group.
            sum     salary,
            average gross_salary,
            sum     gross_salary,
            average gross_cost,
            sum_gross_cost: sum gross_cost,
            row_count: count salary
        ]
        sort sum_gross_cost
        filter row_count > 200
        take 20
        """

        agg_funcs = [
            "AVG(salary)",
            "SUM(salary)",
            "AVG(salary+payroll_tax)",
            "SUM(salary+payroll_tax)",
            "AVG(salary+payroll_tax+benefits_cost)",
            "SUM(salary+payroll_tax+benefits_cost) as sum_gross_cost",
            "COUNT(salary) as row_count",
        ]

        filter_str = 'country="USA"'
        filter_str_2 = "(gross_salary+benefits_cost)>0"
        group_by_str = "GROUP BY title,country"
        havings_str = "HAVING row_count>200"
        order_by_str = "ORDER BY sum_gross_cost "
        limit_str = "LIMIT 20"

        sql = prql.to_sql(text, True)
        # [self.assertTrue(sql.index(f) > 0) for f in agg_funcs]
        # self.assertTrue(sql.index(filter_str) > 0)
        # self.assertTrue(sql.index(filter_str_2) > 0)
        # self.assertTrue(sql.index(group_by_str) > 0)
        # self.assertTrue(sql.index(havings_str) > 0)
        # self.assertTrue(sql.index(order_by_str) > 0)
        # self.assertTrue(sql.index(limit_str) > 0)

        print(sql)
        self.run_query(text)

    def test_cte1(self):
        q = """
        table newest_employees = (
            from employees
            sort tenure
            take 50
        )

        from newest_employees
        join salary [id]
        select [name, salary]
        """
        sql = prql.to_sql(q)
        print(sql)
        # self.run_query(text)

    def test_derive_issue_20(self):
        q = """
        from employees
        select [ benefits_cost , salary, title ]
        aggregate by:title [ ttl_sal: salary | sum ]
        derive [ avg_sal: salary  ]
        sort ttl_sal order:desc | take 25"""
        sql = prql.to_sql(q, True)
        assert sql.index("avg_sal") > 0
        print(sql)
