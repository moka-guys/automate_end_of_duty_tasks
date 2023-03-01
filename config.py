""" Email server settings
"""

import os

DOCUMENT_ROOT = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_DIR = os.path.join(DOCUMENT_ROOT, "templates")
EMAIL_TEMPLATE = "email.html"
LOGGING_FORMATTER = "%(asctime)s - %(levelname)s - %(message)s"

PROJECT_PATTERN = "(project-\S+)__\S+__"

TSO_MESSAGE = "WARNING! TSO500 Results files can take some time to download"

HOST = "email-smtp.eu-west-1.amazonaws.com"
PORT = 587
EMAIL_SENDER = "moka.alerts@gstt.nhs.uk"
EMAIL_RECIPIENT = "gst-tr.mokaguys@nhs.net"
SMTP_DO_TLS = True

RUNTYPE_IDENTIFIERS = {
    "WES": ["WES"],
    "MokaPipe": ["NGS"],
    "SNP": ["SNP"],
    "TSO500": ["TSO"],
}

PER_RUNTYPE_DOWNLOADS = {
    "WES": {
        "exon_level": {
            "folder": "/coverage",
            "regex": "\S+.chanjo_txt$",
        }
    },
    "MokaPipe": {
        "exon_level_coverage": {
            "folder": "/coverage",
            "regex": "\S+.exon_level.txt$",
        },
        "rpkm": {
            "folder": "/conifer_output",
            "regex": "combined_bed_summary\S+",
        },
        "fh_prs": {
            "folder": "/PRS_output",
            "regex": "\S+.txt$",
        },
        "polyedge": {
            "folder": "/polyedge",
            "regex": "\S+_polyedge.pdf$",
        },
    },
    "SNP": {
        "vcfs": {
            "folder": "/output",
            "regex": "\S+.sites_present_reheader_filtered_normalised.vcf$",
        },
    },
    "TSO500": {
        "gene_level_coverage": {
            "folder": "/coverage",
            "regex": "\S+.gene_level.txt$",
        },
        "exon_level_coverage": {
            "folder": "/coverage",
            "regex": "\S+.exon_level.txt$",
        },
        "results_zip": {
            "folder": "/",
            "regex": "^Results.zip$",
        },
        "sompy": {
            "folder": "/QC",
            "regex": "\S+_MergedSmallVariants.genome.vcf.stats.csv$",
        },
    },
}
