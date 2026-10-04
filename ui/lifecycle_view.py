"""
ArchiveX - S3 Lifecycle Policy Builder & Dry-Run Inspector View
"""
import streamlit as st
import pandas as pd
from core.lifecycle_gen import (
    build_lifecycle_rule,
    generate_lifecycle_policy_json,
    generate_lifecycle_policy_xml,
    generate_terraform_snippet,
    dry_run_lifecycle_policy
)
from core.aws_client import S3ClientManager

def render_lifecycle_builder(data: dict):
    st.subheader("⚙️ Amazon S3 Lifecycle Policy Builder & Dry-Run Inspector")
    st.caption("Craft, simulate, and operationalize AWS PutBucketLifecycleConfiguration rules with built-in small object protections.")

    df: pd.DataFrame = data["dataframe"]
    current_bucket = data.get("current_bucket", "enterprise-prod-db-backups-us-east-1")
    is_demo = data.get("is_demo_mode", True)

    tab_builder, tab_dryrun, tab_export = st.tabs(["🛠️ Rule Designer", "🧪 Dry-Run Simulation", "📄 Export Infrastructure Code"])

    # 1. Rule Designer
    with tab_builder:
        st.markdown("#### Configure Lifecycle Optimization Rule")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            rule_id = st.text_input("Rule ID / Name", value="ArchiveX-AutoTier-Backups")
            prefix = st.text_input("Prefix Filter (optional, leave blank for entire bucket)", value="backups/")
            protect_small = st.checkbox("Enforce 128 KB Guardrail (ObjectSizeGreaterThan: 131,072 bytes)", value=True, help="Prevents small files from incurring 128KB minimum capacity billing in Glacier.")

        with col_r2:
            mode = st.radio("Target Strategy", options=["Tiered Archiving (IA -> Glacier -> Deep Archive)", "S3 Intelligent-Tiering (Auto)"])
            enable_it = mode.startswith("S3 Intelligent")
            
            if not enable_it:
                days_ia = st.number_input("Days to S3 Standard-IA", min_value=0, max_value=365, value=30, step=15)
                days_glacier = st.number_input("Days to S3 Glacier Flexible", min_value=0, max_value=730, value=90, step=30)
                days_deep = st.number_input("Days to S3 Glacier Deep Archive", min_value=0, max_value=3650, value=180, step=30)
            else:
                days_ia, days_glacier, days_deep = 0, 0, 0

            days_expire = st.number_input("Days to Object Expiration / Deletion (0 = retain indefinitely)", min_value=0, max_value=3650, value=0, step=30)

        # Build rule dictionary
        min_sz = 131072 if protect_small else 0
        rule = build_lifecycle_rule(
            rule_id=rule_id,
            prefix=prefix,
            min_object_size=min_sz,
            days_to_ia=days_ia,
            days_to_glacier=days_glacier,
            days_to_deep_archive=days_deep,
            days_to_expire=days_expire,
            enable_it=enable_it
        )

        st.session_state["current_lifecycle_rules"] = [rule]
        st.success(f"Rule '{rule_id}' defined and cached for dry-run simulation.")

    # 2. Dry-Run Simulation
    with tab_dryrun:
        st.markdown("#### Dry-Run Impact Assessment")
        st.caption("Validates the configured rule against currently loaded bucket objects without touching AWS.")

        rules = st.session_state.get("current_lifecycle_rules", [rule])
        dry_result = dry_run_lifecycle_policy(df, rules)

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.metric("Objects Evaluated", f"{dry_result['total_evaluated']:,}")
        with d2:
            st.metric("Objects Transitioned", f"{dry_result['affected_count']:,}")
        with d3:
            st.metric("Small Objects Protected (<128KB)", f"{dry_result['small_objects_protected']:,}")
        with d4:
            st.metric("Eligible Volume", f"{dry_result['affected_size_gb']} GB")

        if dry_result["transitions_by_tier"]:
            st.markdown("##### Transitions by Target Storage Class")
            for t_class, cnt in dry_result["transitions_by_tier"].items():
                st.write(f"• **{t_class}**: {cnt:,} objects")

        if dry_result["sample_matches"]:
            st.markdown("##### Simulated Object Transition Preview (First 20 items)")
            st.dataframe(pd.DataFrame(dry_result["sample_matches"][:20]), use_container_width=True)

        st.markdown("---")
        # Apply to AWS (with Safeguards)
        st.subheader("🚀 AWS Deployment")
        if is_demo:
            st.info("ℹ️ **Demo Mode Active:** AWS deployment is simulated. To apply to live S3 buckets, disable Demo Mode in Settings and configure credentials.")
            if st.button("Simulate Policy Application", type="primary"):
                st.success(f"Simulated successfully! Policy {rule_id} validated for bucket '{current_bucket}'.")
        else:
            st.warning("⚠️ **Live AWS Mode Active:** Applying this rule modifies the S3 bucket lifecycle configuration.")
            confirmed = st.checkbox(f"I confirm that I want to apply this lifecycle policy to bucket '{current_bucket}'.")
            
            if st.button("Publish Lifecycle Policy to AWS S3", type="primary", disabled=not confirmed):
                aws_client: S3ClientManager = data.get("aws_client")
                if aws_client:
                    res = aws_client.apply_lifecycle_policy(
                        bucket_name=current_bucket,
                        lifecycle_rules=rules,
                        confirmed=confirmed,
                        dry_run=False
                    )
                    if res.get("status") == "APPLIED_SUCCESSFULLY":
                        st.success(res.get("message"))
                    else:
                        st.error(f"Failed to apply: {res.get('error') or res.get('message')}")
                else:
                    st.error("AWS Client not initialized.")

    # 3. Export Formats
    with tab_export:
        st.markdown("#### Production Infrastructure as Code Export")
        rules = st.session_state.get("current_lifecycle_rules", [rule])
        
        json_policy = generate_lifecycle_policy_json(rules)
        xml_policy = generate_lifecycle_policy_xml(rules)
        tf_policy = generate_terraform_snippet(current_bucket, rules)

        exp_json, exp_xml, exp_tf = st.tabs(["JSON (AWS CLI / SDK)", "XML (S3 API)", "Terraform HCL"])
        
        with exp_json:
            st.code(json_policy, language="json")
            st.download_button("Download lifecycle-policy.json", data=json_policy, file_name="lifecycle-policy.json", mime="application/json")

        with exp_xml:
            st.code(xml_policy, language="xml")
            st.download_button("Download lifecycle-configuration.xml", data=xml_policy, file_name="lifecycle-configuration.xml", mime="application/xml")

        with exp_tf:
            st.code(tf_policy, language="hcl")
            st.download_button("Download main.tf", data=tf_policy, file_name="s3_lifecycle.tf", mime="text/plain")
