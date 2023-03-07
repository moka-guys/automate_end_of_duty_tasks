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
EMAIL_RECIPIENT = "gst-tr.mokaguys@nhs.net"
SMTP_DO_TLS = True

COLS = ["Name", "Folder", "Type", "Url", "GSTT_dir"]

RUNTYPE_IDENTIFIERS = {
    "WES": ["WES"],
    "MokaPipe": ["NGS"],
    "SNP": ["SNP"],
    "TSO500": ["TSO"],
    "ADX": ["ADX"],
    "ONC": ["ONC"],
}

PER_RUNTYPE_DOWNLOADS = {
    "WES": {
        "exon_level": {
            "folder": "/coverage",
            "regex": r"\S+.chanjo_txt$",
        }
    },
    "MokaPipe": {
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
        "results_zip": {
            "folder": "/",
            "regex": r"^(?:{})_Results.zip$",
        },
        "sompy": {
            "folder": "/QC",
            "regex": r"\S+_MergedSmallVariants.genome.vcf.stats.csv$",
        },
    },
    "ADX": False,
    "ONC": False,
}

P_BIOINF_TESTING = "P:\\Bioinformatics\\testing\\process_duty_csv"

GSTT_PATHS = {
    "TEST": {
        "WES": {
            "exon_level": {
                "Via": f"{P_BIOINF_TESTING}\\WES\\genesummaries\\",
                "StG": False,
            }
        },
        "MokaPipe": {
            "exon_level_coverage": {
                "Via": f"{P_BIOINF_TESTING}\\MokaPIPE\\%s\\coverage\\",
                "StG": f"{P_BIOINF_TESTING}\\StG\\%s\\coverage\\",
            },
            "rpkm": {
                "Via": f"{P_BIOINF_TESTING}\\MokaPIPE\\%s\\RPKM\\",
                "StG": f"{P_BIOINF_TESTING}\\StG\\%s\\RPKM\\",
            },
            "fh_prs": {
                "Via": f"{P_BIOINF_TESTING}\\MokaPIPE\\%s\\FH_PRS\\",
                "StG": f"{P_BIOINF_TESTING}\\StG\\%s\\FH_PRS\\",
            },
            "polyedge": {
                "Via": f"{P_BIOINF_TESTING}\\MokaPIPE\\%s\\polyedge\\",
                "StG": f"{P_BIOINF_TESTING}\\StG\\%s\\polyedge\\",
            },
        },
        "SNP": {
            "vcfs": {
                "Via": f"{P_BIOINF_TESTING}\\SNP\\VCFs_Andrew\\",
                "StG": False,
            },
        },
        "TSO500": {
            "gene_level_coverage": {
                "Via": f"{P_BIOINF_TESTING}\\TSO500\\coverage\\",
                "StG": False,
            },
            "exon_level_coverage": {
                "Via": f"{P_BIOINF_TESTING}\\TSO500\\coverage\\",
                "StG": False,
            },
            "results_zip": {
                "Via": f"{P_BIOINF_TESTING}\\TSO500\\Results\\",
                "StG": False,
            },
            "sompy": {
                "Via": f"{P_BIOINF_TESTING}\\TSO500\\sompy\\",
                "StG": False,
            },
        },
    },
    "PROD": {
        "WES": {
            "exon_level": {
                "Via": "S:\\Genetics\\Bioinformatics\\NGS\\depthofcoverage\\genesummaries\\",
                "StG": False,
            },
        },
        "MokaPipe": {
            "exon_level_coverage": {
                "Via": "P:\\DNA LAB\\Current\\NGS worksheets\\%s\\coverage\\",
                "StG": "P:\\DNA LAB\\StG SFTP\\StG SFTP outgoing\\%s\\coverage\\",
            },
            "rpkm": {
                "Via": "P:\\DNA LAB\\Current\\NGS worksheets\\%s\\RPKM\\",
                "StG": "P:\\DNA LAB\\StG SFTP\\StG SFTP outgoing\\%s\\RPKM\\",
            },
            "fh_prs": {
                "Via": "P:\\DNA LAB\\Current\\NGS worksheets\\%s\\FH_PRS\\",
                "StG": "P:\\DNA LAB\\StG SFTP\\StG SFTP outgoing\\%s\\FH_PRS\\",
            },
            "polyedge": {
                "Via": "P:\\DNA LAB\\Current\\NGS worksheets\\%s\\polyedge\\",
                "StG": "P:\\DNA LAB\\StG SFTP\\StG SFTP outgoing\\%s\\polyedge\\",
            },
        },
        "SNP": {
            "vcfs": {
                "Via": "P:\\Bioinformatics\\VCFs_Andrew\\",
                "StG": False,
            },
        },
        "TSO500": {
            "gene_level_coverage": {
                "Via": "S:\\Genetics_Data2\\TSO500\\coverage\\",
                "StG": False,
            },
            "exon_level_coverage": {
                "Via": "S:\\Genetics_Data2\\TSO500\\coverage\\",
                "StG": False,
            },
            "results_zip": {
                "Via": "S:\\Genetics_Data2\\TSO500\\Results\\",
                "StG": False,
            },
            "sompy": {
                "Via": "S:\\Genetics_Data2\\TSO500\\sompy\\",
                "StG": False,
            },
        },
    },
}
