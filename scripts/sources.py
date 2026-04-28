"""
Priority URLs for Citebound corpus.
Sourced from the landscape report Section 1.
"""

PRIORITY_SOURCES = [
    # ─────────────────────────────────────────────────────────────
    # Original 9 sources (Days 2–3)
    # ─────────────────────────────────────────────────────────────
    {
        "id": "study_permit_eligibility",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit/eligibility.html",
        "topic": "study_permit",
        "description": "Who can apply for a study permit"
    },
    {
        "id": "pgwp_eligibility",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/work/after-graduation/eligibility.html",
        "topic": "pgwp",
        "description": "Post-Graduation Work Permit eligibility"
    },
    {
        "id": "off_campus_work",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/work/work-off-campus.html",
        "topic": "working_while_studying",
        "description": "Off-campus work rules including 24-hour limit"
    },
    {
        "id": "express_entry_overview",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry.html",
        "topic": "express_entry",
        "description": "Express Entry overview"
    },
    {
        "id": "express_entry_rounds",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/rounds-invitations.html",
        "topic": "express_entry",
        "description": "Recent rounds of invitations"
    },
    {
        "id": "oinp_overview",
        "url": "https://www.ontario.ca/page/ontario-immigrant-nominee-program-streams",
        "topic": "pnp",
        "description": "Ontario Immigrant Nominee Program streams"
    },
    {
        "id": "cra_international_students",
        "url": "https://www.canada.ca/en/revenue-agency/services/tax/international-non-residents/individuals-leaving-entering-canada-non-residents/international-students-studying-canada.html",
        "topic": "tax",
        "description": "CRA tax info for international students"
    },
    {
        "id": "ohip_eligibility",
        "url": "https://www.ontario.ca/page/apply-ohip-and-get-health-card",
        "topic": "health",
        "description": "OHIP eligibility and application"
    },
    {
        "id": "pal_requirements",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit/get-documents/provincial-attestation-letter.html",
        "topic": "study_permit",
        "description": "Provincial Attestation Letter requirements"
    },
    {
        "id": "oinp_masters_graduate",
        "url": "https://www.ontario.ca/page/oinp-masters-graduate-stream",
        "topic": "pnp",
        "description": "OINP Masters Graduate stream"
    },
    {
        "id": "cra_residency_status",
        "url": "https://www.canada.ca/en/revenue-agency/services/tax/international-non-residents/information-been-moved/determining-your-residency-status.html",
        "topic": "tax",
        "description": "Determining your residency status for tax purposes"
    },

    # ─────────────────────────────────────────────────────────────
    # Study permits and PGWP
    # ─────────────────────────────────────────────────────────────
    {
        "id": "study_canada_hub",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada.html",
        "topic": "study_permit",
        "description": "Master hub for studying in Canada"
    },
    {
        "id": "extend_study_permit",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/extend-study-permit.html",
        "topic": "study_permit",
        "description": "Extending a study permit, restoration of status"
    },
    {
        "id": "dli_list",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit/prepare/designated-learning-institutions-list.html",
        "topic": "study_permit",
        "description": "Designated Learning Institutions list"
    },
    {
        "id": "work_while_studying",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/work.html",
        "topic": "working_while_studying",
        "description": "Working as an international student overview"
    },
    {
        "id": "coop_work_permit_guide",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/application/application-forms-guides/guide-5580-applying-work-permit-student-guide-paper.html",
        "topic": "working_while_studying",
        "description": "Work permit student guide (covers co-op rules including April 2026 elimination for post-secondary)"
    },

    # ─────────────────────────────────────────────────────────────
    # Express Entry
    # ─────────────────────────────────────────────────────────────
    {
        "id": "express_entry_eligibility",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/eligibility.html",
        "topic": "express_entry",
        "description": "Express Entry eligibility for FSW, CEC, FST"
    },
    {
        "id": "express_entry_categories",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/rounds-invitations/category-based-selection.html",
        "topic": "express_entry",
        "description": "Category-based selection draws"
    },
    {
        "id": "express_entry_job_offer",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/documents/job-offer.html",
        "topic": "express_entry",
        "description": "Job offer rules post-March 2025"
    },

    # ─────────────────────────────────────────────────────────────
    # CRA tax
    # ─────────────────────────────────────────────────────────────
    {
        "id": "cra_students_hub",
        "url": "https://www.canada.ca/en/revenue-agency/services/tax/individuals/segments/students.html",
        "topic": "tax",
        "description": "CRA student tax hub"
    },
    {
        "id": "cra_newcomers",
        "url": "https://www.canada.ca/en/revenue-agency/services/tax/international-non-residents/individuals-leaving-entering-canada-non-residents/newcomers-canada-immigrants.html",
        "topic": "tax",
        "description": "CRA newcomers to Canada"
    },
    {
        "id": "cra_gst_hst_credit",
        "url": "https://www.canada.ca/en/revenue-agency/services/child-family-benefits/goods-services-tax-harmonized-sales-tax-gst-hst-credit.html",
        "topic": "tax",
        "description": "GST/HST credit eligibility"
    },
    {
        "id": "cra_residency_t1261",
        "url": "https://www.canada.ca/en/revenue-agency/services/forms-publications/forms/t1261.html",
        "topic": "tax",
        "description": "CRA Form T1261 — Individual Tax Number for non-residents"
    },
    {
        "id": "cra_nr74",
        "url": "https://www.canada.ca/en/revenue-agency/services/forms-publications/forms/nr74.html",
        "topic": "tax",
        "description": "CRA Form NR74 — Determination of Residency Status"
    },
    {
        "id": "cra_tfsa",
        "url": "https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/tax-free-savings-account.html",
        "topic": "tax",
        "description": "TFSA basics — note non-resident contribution penalty"
    },
    {
        "id": "cra_rc151",
        "url": "https://www.canada.ca/en/revenue-agency/services/forms-publications/forms/rc151.html",
        "topic": "tax",
        "description": "CRA Form RC151 — GST/HST credit for newcomers"
    },

    # ─────────────────────────────────────────────────────────────
    # Provincial Nominee Programs (PNPs)
    # ─────────────────────────────────────────────────────────────
    {
        "id": "bc_pnp",
        "url": "https://www.welcomebc.ca/immigrate-to-b-c",
        "topic": "pnp",
        "description": "BC Provincial Nominee Program"
    },
    {
        "id": "alberta_aaip",
        "url": "https://www.alberta.ca/alberta-advantage-immigration-program",
        "topic": "pnp",
        "description": "Alberta Advantage Immigration Program"
    },
    {
        "id": "manitoba_mpnp",
        "url": "https://immigratemanitoba.com",
        "topic": "pnp",
        "description": "Manitoba Provincial Nominee Program"
    },
    {
        "id": "nova_scotia_nsnp",
        "url": "https://novascotiaimmigration.com",
        "topic": "pnp",
        "description": "Nova Scotia Nominee Program"
    },
    {
        "id": "oinp_employer_job_offer",
        "url": "https://www.ontario.ca/page/oinp-employer-job-offer-international-student-stream",
        "topic": "pnp",
        "description": "OINP Employer Job Offer International Student Stream"
    },
    {
        "id": "oinp_phd_graduate",
        "url": "https://www.ontario.ca/page/oinp-phd-graduate-stream",
        "topic": "pnp",
        "description": "OINP PhD Graduate stream"
    },
    {
        "id": "oinp_2026_updates",
        "url": "https://www.ontario.ca/page/2026-ontario-immigrant-nominee-program-updates",
        "topic": "pnp",
        "description": "OINP 2026 program updates"
    },

    # ─────────────────────────────────────────────────────────────
    # Quebec immigration
    # ─────────────────────────────────────────────────────────────
    {
        "id": "quebec_pstq",
        "url": "https://www.quebec.ca/en/immigration/permanent/skilled-workers/skilled-worker-selection-program/requirements",
        "topic": "pnp",
        "description": "Quebec PSTQ skilled worker program (replaced PEQ)"
    },
    {
        "id": "quebec_caq",
        "url": "https://www.quebec.ca/en/education/study-quebec/temporary-selection-studies",
        "topic": "study_permit",
        "description": "Quebec CAQ — application for temporary selection for studies"
    },

    # ─────────────────────────────────────────────────────────────
    # Provincial health coverage
    # ─────────────────────────────────────────────────────────────
    {
        "id": "bc_msp",
        "url": "https://www2.gov.bc.ca/gov/content/health/health-drug-coverage/msp/bc-residents/eligibility-and-enrolment",
        "topic": "health",
        "description": "BC Medical Services Plan eligibility"
    },
    {
        "id": "alberta_ahcip",
        "url": "https://www.alberta.ca/ahcip-students",
        "topic": "health",
        "description": "Alberta Health Care Insurance for students"
    },
    {
        "id": "quebec_ramq",
        "url": "https://www.ramq.gouv.qc.ca/en/foreign-students-register-health-insurance-online",
        "topic": "health",
        "description": "Quebec RAMQ for foreign students"
    },
    {
        "id": "manitoba_health",
        "url": "https://www.gov.mb.ca/health/mhsip/eligibility.html",
        "topic": "health",
        "description": "Manitoba Health eligibility"
    },
    {
        "id": "nova_scotia_msi",
        "url": "https://novascotia.ca/dhw/msi/eligibility.asp",
        "topic": "health",
        "description": "Nova Scotia MSI eligibility"
    },

    # ─────────────────────────────────────────────────────────────
    # Operational
    # ─────────────────────────────────────────────────────────────
    {
        "id": "processing_times",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/application/check-processing-times.html",
        "topic": "operational",
        "description": "IRCC processing times"
    },
    {
        "id": "ircc_fees",
        "url": "https://ircc.canada.ca/english/information/fees/fees.asp",
        "topic": "operational",
        "description": "IRCC fee schedule"
    },
    {
        "id": "biometrics",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/biometrics.html",
        "topic": "operational",
        "description": "Biometrics overview — who needs to give them"
    },
    {
        "id": "medical_exams",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/application/medical-police/medical-exams.html",
        "topic": "operational",
        "description": "Immigration medical exams"
    },
    {
        "id": "transition_binder",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/corporate/transparency/transition-binders/minister-2025-05/international-student-program.html",
        "topic": "study_permit",
        "description": "IRCC Minister 2025 transition binder — international students"
    },
]