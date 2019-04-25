import json
import asyncio
from pitcrew import task


@task.arg("zone_id", desc="The zone id to operate on", type=str)
@task.arg("records", desc="A list of records to ensure are set", type=list)
class HasRecords(task.BaseTask):
    """Ensure route53 has the set of records"""

    async def verify(self):
        json_out = await self.sh(
            f"aws route53 list-resource-record-sets --hosted-zone-id {self.params.esc_zone_id}"
        )
        out = json.loads(json_out)
        existing_record_sets = out["ResourceRecordSets"]
        for record in self.params.records:
            assert record in existing_record_sets, "cannot find record"

    async def run(self):
        changes = map(
            lambda c: {"Action": "UPSERT", "ResourceRecordSet": c}, self.params.records
        )
        change_batch = {"Changes": list(changes)}
        change_id = json.loads(
            await self.sh(
                f"aws route53 change-resource-record-sets --hosted-zone-id {self.params.esc_zone_id} --change-batch {self.esc(json.dumps(change_batch))}"
            )
        )["ChangeInfo"]["Id"]
        while (
            json.loads(
                await self.sh(f"aws route53 get-change --id {self.esc(change_id)}")
            )["ChangeInfo"]["Status"]
            == "PENDING"
        ):
            await asyncio.sleep(5)
