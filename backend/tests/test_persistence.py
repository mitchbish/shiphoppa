from datetime import date, timedelta

from app.algorithms import submit_booking
from app.models import (
    ActorRole,
    BookingCreate,
    CargoCategory,
    SEOAudience,
    SEOOpportunityCreate,
    SEOPageType,
    SEOTargetCountry,
    ServiceLevel,
    SourceMessageCreate,
)
from app.operations import create_seo_opportunity, ingest_source_message
from app.persistence import load_store_snapshot, save_store_snapshot
from app.seed import seed_data
from app.store import Store


def test_store_snapshot_round_trips_operating_backbone(tmp_path) -> None:
    store = Store()
    seed_data(store)

    match = submit_booking(
        store,
        BookingCreate(
            importer_company_name="Bayside Build Co.",
            importer_contact_name="Alex Morgan",
            importer_email="snapshot@example.com",
            supplier_name="Dongguan Home Furnishings",
            supplier_city="Dongguan",
            supplier_province="Guangdong",
            supplier_country="China",
            delivery_city="Brisbane",
            delivery_postcode="4101",
            delivery_country="Australia",
            cargo_description="flat-pack vanities and bathroom cabinets",
            cargo_category=CargoCategory.furniture,
            cbm_estimate=10,
            weight_kg_estimate=2200,
            cargo_ready_date_earliest=date.today() + timedelta(days=1),
            cargo_ready_date_latest=date.today() + timedelta(days=5),
            service_level=ServiceLevel.standard,
        ),
        actor_id="snapshot-test",
    )
    message = ingest_source_message(
        store,
        SourceMessageCreate(
            from_address="sales@dongguan-home.example",
            to_addresses=["imports@shiphoppa.com"],
            subject=f"Packing list for {match.booking.id}",
            body="Attached is the packing list for the order.",
            attachment_names=["packing-list.xlsx"],
        ),
        ActorRole.importer,
        "snapshot-test",
    )
    opportunity = create_seo_opportunity(
        store,
        SEOOpportunityCreate(
            target_country=SEOTargetCountry.china,
            audience=SEOAudience.supplier,
            category="furniture",
            city="Foshan",
            lane="China to Australia",
            keyword_cluster=["Foshan furniture exporters", "Australia buyers"],
            opportunity_score=88,
            page_type=SEOPageType.supplier_landing,
        ),
        actor_id="ops",
    )

    snapshot_path = tmp_path / "store_snapshot.json"
    save_store_snapshot(store, snapshot_path)

    restored = Store()
    assert load_store_snapshot(restored, snapshot_path) is True

    assert match.booking.id in restored.bookings
    assert message.id in restored.source_messages
    assert opportunity.id in restored.seo_opportunities
    assert restored.import_projects
    assert restored.import_project_versions
    assert restored.automation_runs
    assert restored.supplier_discovery_runs
    assert restored.supplier_leads
    assert restored.next_id("BKG") != match.booking.id
