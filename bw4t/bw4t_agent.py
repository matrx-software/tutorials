from matrx.agents import AgentBrain

from bw4t.state import State


class BlockWorldAgent(AgentBrain):

    def __init__(self, memorize_for_ticks=10):
        self.__memorize_for_ticks = memorize_for_ticks
        self.__collect = None
        self.state = None
        super().__init__()

    def initialize(self):
        self.state = State(memorize_for_ticks=self.__memorize_for_ticks)

    def filter_observations(self, state_dict):
        self.state.update(state_dict)
        me = self.state[self.agent_name]
        found = self.state.get_with_property("obj_id", self.agent_id)
        if self.__collect is None:
            pass
        return self.state.as_dict()

    def decide_on_action(self, state_dict):
        return None, {}
