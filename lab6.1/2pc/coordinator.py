"""
Implementation of the 3-Phase Commit Protocol (3PC).
Extensions made to existing 2PC protocol to include:
- Precommit phase in the coordinator.
- Additional states and messages for participants.
- Enhanced fault-tolerance for coordinator failures.
"""

import random
import logging
import stablelog

# coordinator messages
from const2PC import VOTE_REQUEST, PREPARE_COMMIT, GLOBAL_COMMIT, GLOBAL_ABORT
# participant messages
from const2PC import VOTE_COMMIT, VOTE_ABORT, READY_COMMIT, NEED_DECISION
# misc constants
from const2PC import TIMEOUT

class Coordinator:
    """
    Implements a three-phase commit coordinator.
    - Introduces a PRECOMMIT state.
    - Enhanced fault-tolerance by involving READY_COMMIT messages.
    """

    def __init__(self, chan):
        self.channel = chan
        self.coordinator = self.channel.join('coordinator')
        self.participants = []  # list of all participants
        self.log = stablelog.create_log("coordinator-" + self.coordinator)
        self.stable_log = stablelog.create_log("coordinator-"
                                               + self.coordinator)
        self.logger = logging.getLogger("vs2lab.lab6.3pc.Coordinator")
        self.state = None

    def _enter_state(self, state):
        self.stable_log.info(state)  # Write to recoverable persistent log file
        self.logger.info("Coordinator {} entered state {}."
                         .format(self.coordinator, state))
        self.state = state

    def init(self):
        self.channel.bind(self.coordinator)
        self._enter_state('INIT')  # Start in INIT state.

        # Prepare participant information.
        self.participants = self.channel.subgroup('participant')

    def run(self):
        # Simulate possible crash before voting
        if random.random() > 3/4:
            return "Coordinator crashed in state INIT."

        # Phase 1: Request votes
        self._enter_state('WAIT')
        self.channel.send_to(self.participants, VOTE_REQUEST)

        if random.random() > 2/3:
            return "Coordinator crashed in state WAIT."

        # Collect votes
        votes = []
        for _ in range(len(self.participants)):
            msg = self.channel.receive_from(self.participants, TIMEOUT)

            if not msg or msg[1] == VOTE_ABORT:
                reason = "timeout" if not msg else f"local_abort from {msg[0]}"
                self._enter_state('ABORT')
                self.channel.send_to(self.participants, GLOBAL_ABORT)
                return f"Coordinator {self.coordinator} terminated in state ABORT. Reason: {reason}."

            assert msg[1] == VOTE_COMMIT
            votes.append(msg[0])

        # Phase 2: Precommit
        self._enter_state('PRECOMMIT')
        self.channel.send_to(self.participants, PREPARE_COMMIT)

        # Collect READY_COMMIT acknowledgments
        ready_count = 0
        for _ in range(len(self.participants)):
            msg = self.channel.receive_from(self.participants, TIMEOUT)
            if not msg or msg[1] != READY_COMMIT:
                reason = "timeout" if not msg else f"unexpected message {msg[1]}"
                self._enter_state('ABORT')
                self.channel.send_to(self.participants, GLOBAL_ABORT)
                return f"Coordinator {self.coordinator} terminated in state ABORT. Reason: {reason}."

            ready_count += 1

        assert ready_count == len(self.participants)

        # Phase 3: Commit
        self._enter_state('COMMIT')
        self.channel.send_to(self.participants, GLOBAL_COMMIT)
        return f"Coordinator {self.coordinator} terminated in state COMMIT."