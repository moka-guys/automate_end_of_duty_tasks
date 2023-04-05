""" Config file for duty_csv
"""

import os

DOCUMENT_ROOT = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_DIR = os.path.join(DOCUMENT_ROOT, "templates")
EMAIL_TEMPLATE = "email.html"
LOGGING_FORMATTER = "%(asctime)s - %(levelname)s - %(message)s"

PROJECT_PATTERN = r"(project-\S+)__\S+__"

EMAIL_SUBJECT = {
    "TEST": "TEST MODE. {} run: {}",
    "PROD": "{} run: {}",
}

HOST = "email-smtp.eu-west-1.amazonaws.com"
PORT = 587
EMAIL_SENDER = "moka.alerts@gstt.nhs.uk"
EMAIL_RECIPIENT = {
    "TEST": "mokaguys@gmail.com",
    "PROD": "gst-tr.mokaguys@nhs.net",
}
SMTP_DO_TLS = True

COLS = ["Name", "Folder", "Type", "Url", "GSTT_dir", "subdir"]

# Signifies what identifies the runfolder name as being that run type - both
# substrings that must be present and substrings that must be absent
RUNTYPE_IDENTIFIERS = {
    "WES": {"present": ["WES", "NGS"], "absent": []},
    "CustomPanels": {"present": ["NGS"], "absent": ["WES"]},
    "LRPCR": {"present": ["LRPCR"], "absent": []},
    "SNP": {"present": ["SNP"], "absent": []},
    "TSO500": {"present": ["TSO"], "absent": []},
    "ArcherDX": {"present": ["ADX"], "absent": []},
    "SWIFT": {"present": ["ONC"], "absent": []},
}

PER_RUNTYPE_DOWNLOADS = {
    "WES": {
        "exon_level": {
            "folder": "/coverage",
            "regex": r"\S+.chanjo_txt$",
        }
    },
    **dict.fromkeys(
        ["CustomPanels", "LRPCR"],
        {
            "exon_level_coverage": {
                "folder": "/coverage",
                "regex": r"\S+.exon_level.txt$",
            },
            "rpkm": {
                "folder": "/conifer_output",
                "regex": r"combined_bed_summary\S+",
            },
            "fh_prs": {
                "folder": "/PRS_output",
                "regex": r"\S+.txt$",
            },
            "polyedge": {
                "folder": "/polyedge",
                "regex": r"\S+_polyedge.pdf$",
            },
        },
    ),
    "SNP": {
        "vcfs": {
            "folder": "/output",
            "regex": r"\S+.sites_present_reheader_filtered_normalised.vcf$",
        },
    },
    "TSO500": {
        "gene_level_coverage": {
            "folder": "/coverage",
            "regex": r"\S+(?:{}).gene_level.txt$",
        },
        "exon_level_coverage": {
            "folder": "/coverage",
            "regex": r"\S+(?:{}).exon_level.txt$",
        },
        "sompy": {
            "folder": "/QC",
            "regex": r"\S+_MergedSmallVariants.genome.vcf.stats.csv$",
        },
        "results_zip": {
            "folder": "/",
            "regex": r"^(?:{})_Results.zip$",
        },
    },
    **dict.fromkeys(["ArcherDX", "SWIFT"], False),
}

P_BIOINF_TESTING = "P:/Bioinformatics/testing/process_duty_csv"

GSTT_PATHS = {
    "TEST": {
        "WES": {
            "exon_level": {
                "Via": f"{P_BIOINF_TESTING}/WES/genesummaries/",
                "StG": False,
                "subdir": None,
            }
        },
        **dict.fromkeys(
            ["CustomPanels", "LRPCR"],
            {
                "exon_level_coverage": {
                    "Via": f"{P_BIOINF_TESTING}/CustomPanels/%s%s/",
                    "StG": f"{P_BIOINF_TESTING}/StG/%s/",
                    "subdir": r"coverage/",
                },
                "rpkm": {
                    "Via": f"{P_BIOINF_TESTING}/CustomPanels/%s%s/",
                    "StG": f"{P_BIOINF_TESTING}/StG/%s/",
                    "subdir": r"RPKM/",
                },
                "fh_prs": {
                    "Via": f"{P_BIOINF_TESTING}/CustomPanels/%s%s/",
                    "StG": f"{P_BIOINF_TESTING}/StG/%s/",
                    "subdir": r"FH_PRS/",
                },
                "polyedge": {
                    "Via": f"{P_BIOINF_TESTING}/CustomPanels/%s%s/",
                    "StG": f"{P_BIOINF_TESTING}/StG/%s/",
                    "subdir": r"polyedge/",
                },
            },
        ),
        "SNP": {
            "vcfs": {
                "Via": f"{P_BIOINF_TESTING}/SNP/VCFs_Andrew/",
                "StG": False,
                "subdir": None,
            },
        },
        "TSO500": {
            "gene_level_coverage": {
                "Via": f"{P_BIOINF_TESTING}/TSO500/%s/",
                "StG": False,
                "subdir": r"coverage/",
            },
            "exon_level_coverage": {
                "Via": f"{P_BIOINF_TESTING}/TSO500/%s/",
                "StG": False,
                "subdir": r"coverage/",
            },
            "sompy": {
                "Via": f"{P_BIOINF_TESTING}/TSO500/%s/",
                "StG": False,
                "subdir": r"sompy/",
            },
            "results_zip": {
                "Via": f"{P_BIOINF_TESTING}/TSO500/%s/",
                "StG": False,
                "subdir": r"Results/",
            },
        },
        **dict.fromkeys(["ArcherDX", "ONC"], False),
    },
    "PROD": {
        "WES": {
            "exon_level": {
                "Via": "S:/Genetics/Bioinformatics/NGS/depthofcoverage/genesummaries/",
                "StG": False,
                "subdir": None,
            },
        },
        **dict.fromkeys(
            ["CustomPanels", "LRPCR"],
            {
                "exon_level_coverage": {
                    "Via": "P:/DNA LAB/Current/NGS worksheets/%s%s/",
                    "StG": "P:/DNA LAB/StG SFTP/StG SFTP outgoing/%s/",
                    "subdir": r"coverage/",
                },
                "rpkm": {
                    "Via": "P:/DNA LAB/Current/NGS worksheets/%s%s/",
                    "StG": "P:/DNA LAB/StG SFTP/StG SFTP outgoing/%s/",
                    "subdir": r"RPKM/",
                },
                "fh_prs": {
                    "Via": "P:/DNA LAB/Current/NGS worksheets/%s%s/",
                    "StG": "P:/DNA LAB/StG SFTP/StG SFTP outgoing/%s/",
                    "subdir": r"FH_PRS/",
                },
                "polyedge": {
                    "Via": "P:/DNA LAB/Current/NGS worksheets/%s%s/",
                    "StG": "P:/DNA LAB/StG SFTP/StG SFTP outgoing/%s/",
                    "subdir": r"polyedge/",
                },
            },
        ),
        "SNP": {
            "vcfs": {
                "Via": "P:/Bioinformatics/VCFs_Andrew/",
                "StG": False,
                "subdir": None,
            },
        },
        "TSO500": {
            "gene_level_coverage": {
                "Via": "S:/Genetics_Data2/TSO500/%s/",
                "StG": False,
                "subdir": r"coverage/",
            },
            "exon_level_coverage": {
                "Via": "S:/Genetics_Data2/TSO500/%s/",
                "StG": False,
                "subdir": r"coverage/",
            },
            "results_zip": {
                "Via": "S:/Genetics_Data2/TSO500/%s/",
                "StG": False,
                "subdir": r"Results/",
            },
            "sompy": {
                "Via": "S:/Genetics_Data2/TSO500/%s/",
                "StG": False,
                "subdir": r"sompy/",
            },
        },
        **dict.fromkeys(["ArcherDX", "SWIFT"], False),
    },
}
