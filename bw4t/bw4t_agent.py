from matrx.agents import AgentBrain


class BlockWorldAgent(AgentBrain):

    def __init__(self):
        super().__init__()

    def initialize(self):
        pass

    def filter_observations(self, state):
        return state

    def decide_on_action(self, state):
        return None, {}
