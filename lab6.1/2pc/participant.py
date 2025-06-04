import random
import logging
import time

# coordinator messages
from const2PC import VOTE_REQUEST, PREPARE_COMMIT, GLOBAL_COMMIT, GLOBAL_ABORT
# participant decissions
from const2PC import LOCAL_SUCCESS, LOCAL_ABORT
# participant messages
from const2PC import VOTE_COMMIT, VOTE_ABORT, READY_COMMIT, NEED_DECISION
# misc constants
from const2PC import TIMEOUT

import stablelog


class Participant:
    """
    Implements a three-phase commit participant.
    - Includes a PRECOMMIT state.
    - Responds with READY_COMMIT after PREPARE_COMMIT.
    """

    def __init__(self, chan):
        self.channel = chan
        self.participant = self.channel.join('participant')
        self.stable_log = stablelog.create_log(
            "participant-" + self.participant)
        self.logger = logging.getLogger("vs2lab.lab6.3pc.Participant")
        self.coordinator = {}
        self.all_participants = {}
        self.state = 'NEW'

    @staticmethod
    def _do_work():
        # Simulate local activities that may succeed or not
        return LOCAL_ABORT if random.random() > 2/3 else LOCAL_SUCCESS

    def _enter_state(self, state):
        self.stable_log.info(state)  # Write to recoverable persistent log file
        self.logger.info("Participant {} entered state {}."
                         .format(self.participant, state))
        self.state = state

    def init(self):
        self.channel.bind(self.participant)
        self.coordinator = self.channel.subgroup('coordinator')
        self.all_participants = self.channel.subgroup('participant')
        self._enter_state('INIT')  # Start in local INIT state.

    def _elect_new_coordinator(self):
        """Elect a new coordinator and inform all participants."""
        # Elect the participant with the lowest ID as the new coordinator
        new_coordinator = sorted(self.all_participants)[0]  # Example criterion: lowest ID
        self.coordinator = {new_coordinator}
        self.logger.info("Participant {} elected as new coordinator.".format(new_coordinator))

        if self.participant == new_coordinator:
            # New coordinator responsibilities
            self.logger.info("Participant {} acting as new coordinator.".format(self.participant))
            for participant in self.all_participants:
                if participant != self.participant:  # Skip self
                    self.channel.send_to({participant}, TIMEOUT)
            self._handle_as_new_coordinator()
        else:
            # Inform the new coordinator of the participant's state
            self.channel.send_to(self.coordinator, self.state)

    def _handle_as_new_coordinator(self):
        """Handle responsibilities as the new coordinator."""
        states = {}

        # Warten, um sicherzustellen, dass alle Teilnehmer genug Zeit zum Senden ihrer Nachrichten haben
        print("Waiting for participants to respond...")
        time.sleep(2)  # Beispiel: 2 Sekunden warten, um Nachrichten zu sammeln

        # Collect states from all participants
        for participant in self.all_participants:
            if participant != self.participant:  # Skip self
                msg = self.channel.receive_from({participant}, TIMEOUT)
                print(f"Msg: {msg}")
                if msg:
                    states[participant] = msg[1]

        print(states)
        print(f"my state: {self.state}")

        # Synchronize states and determine global decision
        if self.state == 'READY' and all(state in ['INIT', 'READY', 'ABORT', 'PRECOMMIT'] for state in states.values()):
            self._enter_state('ABORT')
            self.channel.send_to(self.all_participants, GLOBAL_ABORT)
        elif self.state == 'PRECOMMIT' and all(state in ['READY', 'PRECOMMIT', 'COMMIT'] for state in states.values()):
            self._enter_state('COMMIT')
            self.channel.send_to(self.all_participants, GLOBAL_COMMIT)
        elif self.state in ['COMMIT', 'ABORT']:
            # Fall 3: Already in a final state, propagate it
            self.channel.send_to(self.all_participants, GLOBAL_COMMIT if self.state == 'COMMIT' else GLOBAL_ABORT)
        else:
            self.logger.error("Inconsistent states detected, unable to terminate.")


    def run(self):
        # Wait for the coordinator's VOTE_REQUEST
        msg = self.channel.receive_from(self.coordinator, TIMEOUT)

        if not msg or msg[1] != VOTE_REQUEST:
            self._elect_new_coordinator()
            return "Coordinator failed during VOTE_REQUEST, new coordinator elected."

        # Phase 1: Local decision
        decision = self._do_work()

        if decision == LOCAL_ABORT:
            self.channel.send_to(self.coordinator, VOTE_ABORT)
        else:
            assert decision == LOCAL_SUCCESS
            self._enter_state('READY')
            self.channel.send_to(self.coordinator, VOTE_COMMIT)

            # Phase 2: Wait for PREPARE_COMMIT
            msg = self.channel.receive_from(self.coordinator, TIMEOUT)
            if not msg or msg[1] != PREPARE_COMMIT:
                self._elect_new_coordinator()
                #return "Coordinator failed during PREPARE_COMMIT, new coordinator elected."

            self._enter_state('PRECOMMIT')
            self.channel.send_to(self.coordinator, READY_COMMIT)

            # Phase 3: Wait for GLOBAL_COMMIT or GLOBAL_ABORT
            msg = self.channel.receive_from(self.coordinator, TIMEOUT)
            if not msg:
                self._elect_new_coordinator()
                #return "Coordinator failed during final phase, new coordinator elected."
            decision = GLOBAL_ABORT if not msg else msg[1]

        # Finalize based on the decision
        if decision == GLOBAL_COMMIT:
            self._enter_state('COMMIT')
        else:
            assert decision in [GLOBAL_ABORT, LOCAL_ABORT]
            self._enter_state('ABORT')

        # Help others if coordinator crashes
        num_of_others = len(self.all_participants) - 1
        while num_of_others > 0:
            num_of_others -= 1
            msg = self.channel.receive_from(self.all_participants, TIMEOUT * 2)
            if msg and msg[1] == NEED_DECISION:
                self.channel.send_to({msg[0]}, decision)

        return "Participant {} terminated in state {} due to {}.".format(
            self.participant, self.state, decision)

