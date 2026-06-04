"""LoRA / Modelfile export pipeline tests."""

from src.blank_business_builder.role_training_pipeline import (
    RoleTrainingPipeline,
    MIN_LABELS_FOR_LORA,
)


def test_judge_export_not_ready_below_threshold():
    pipeline = RoleTrainingPipeline("SaaS Micro-Tools Empire", min_labels=MIN_LABELS_FOR_LORA)
    export = pipeline.export_judge_modelfile(domain="sales")
    assert export.example_count < MIN_LABELS_FOR_LORA
    assert export.ready is False
    assert "Modelfile" in export.modelfile_path
