"""Workflow compiler/validator compatibility without provider execution."""

import copy
import unittest

from zeo_integrations.hubspot.models import EmailSequence, SequenceStep
from zeo_integrations.hubspot.workflow import validate_workflow


class Workflow(unittest.TestCase):
    def flow(self):
        return EmailSequence(
            name="linear",
            steps=(
                SequenceStep(email_id="one"),
                SequenceStep(email_id="two", delay_minutes=5),
            ),
            suppression_list_ids=(1,),
        ).to_api()

    def test_supported_graph_round_trip(self):
        flow = self.flow()
        self.assertFalse(flow["isEnabled"])
        result = validate_workflow(flow)
        self.assertEqual(result.steps[1].delay_minutes, 5)
        self.assertEqual(result.to_api(), flow)

    def test_unknown_trigger_setting_and_reenrollment_refused(self):
        for key, value in [
            ("unknownTrigger", {}),
            ("canEnrollFromSalesforce", True),
            ("enrollmentCriteria", {"type": "MANUAL", "shouldReEnroll": True}),
        ]:
            flow = self.flow()
            flow[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_workflow(flow)

    def test_branch_unknown_action_and_dangling_delay_refused(self):
        original = self.flow()
        variants = []
        for action_key, value in [
            ("actionTypeId", "unknown"),
            ("connection", {"edgeType": "BRANCH", "nextActionId": "3"}),
            ("actionTypeVersion", True),
        ]:
            flow = copy.deepcopy(original)
            flow["actions"][0][action_key] = value
            variants.append(flow)
        dangling = copy.deepcopy(original)
        dangling["actions"] = dangling["actions"][:2]
        dangling["actions"][-1].pop("connection")
        variants.append(dangling)
        for flow in variants:
            with self.subTest(flow=flow), self.assertRaises(ValueError):
                validate_workflow(flow)

    def test_null_optional_decorations_only(self):
        flow = self.flow()
        flow["enrollmentSchedule"] = None
        self.assertEqual(validate_workflow(flow).to_api(), self.flow())
        flow["enrollmentSchedule"] = {}
        with self.assertRaises(ValueError):
            validate_workflow(flow)
