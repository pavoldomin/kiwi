# Copyright (c) 2015 SUSE Linux GmbH.  All rights reserved.
#
# This file is part of kiwi.
#
# kiwi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kiwi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kiwi.  If not, see <http://www.gnu.org/licenses/>
#
import importlib

# project
from ..logger import log

from ..exceptions import (
    KiwiSatSolverPluginError,
    KiwiSatSolverJobError
)


class Sat(object):
    """
    Sat Solver class to run package solver operations

    The class uses SUSE's libsolv sat plugin
    """
    def __init__(self):
        """
        An instance of Sat auto loads the python solv plugin which is a
        python binding to the libsolv C library. An exception is raised
        if the module failed to load. On success a new solver pool is
        initialized for this instance
        """
        try:
            self.solv = importlib.import_module('solv')
            self.Pool = getattr(
                importlib.import_module('solv', 'Pool'), 'Pool'
            )
            self.Selection = getattr(
                importlib.import_module('solv', 'Selection'), 'Selection'
            )
        except Exception as e:
            raise KiwiSatSolverPluginError(
                '{0}: {1}'.format(type(e).__name__, format(e))
            )

        self.pool = self.Pool()
        self.pool.setarch()

    def add_repository(self, solver_repository):
        """
        Add a repository solvable to the pool. This basically add the
        required repository metadata which is needed to run a solver
        operation later.

        :param object solver_repository: Instance of SolverRepository
        """
        solvable = solver_repository.create_repository_solvable(
            '/home/ms/__bob'
        )
        solver_repository = self.pool.add_repo(solver_repository.uri.uri)
        solver_repository.add_solv(solvable)
        self.pool.addfileprovides()
        self.pool.createwhatprovides()

    def solve(self, job_names, skip_missing=False):
        """
        Solve dependencies for the given job list. The list is allowd
        to contain element names of the following format:

        * name
          describes a package name

        * pattern:name
          describes a package collection name whose metadata type
          is called 'pattern' and stored as such in the repository
          metadata. Usually SUSE repos uses that

        * group:name
          describes a package collection name whose metadata type
          is called 'group' and stored as such in the repository
          metadata. Usually RHEL/CentOS/Fedora repos uses that

        :param list job_names: list of strings
        :param bool skip_missing: skip job if not found

        :rtype: dict
        :return: Transaction result information
        """
        solver = self.pool.Solver()
        solver_problems = solver.solve(
            self._setup_jobs(job_names, skip_missing)
        )
        self.solver_problems = self._evaluate_solver_problems(
            solver_problems
        )

        solver_transaction = solver.transaction()
        self.solver_result = self._evaluate_solver_result(
            solver_transaction
        )

    def _evaluate_solver_problems(self, solver_problems):
        pass

    def _evaluate_solver_result(self, solver_transaction):
        pass

    def _setup_jobs(self, job_names, skip_missing):
        jobs = []
        for job_name in job_names:
            selection = self.pool.select(
                job_name, self.Selection.SELECTION_NAME
            )
            if not selection:
                if skip_missing:
                    log.info(
                        '--> Package {0} not found: skipped'.format(job_name)
                    )
                else:
                    raise KiwiSatSolverJobError(
                        'Package {0} not found'.format(job_name)
                    )
            jobs += selection.jobs(self.solv.Job.SOLVER_INSTALL)
        return jobs
