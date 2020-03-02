# -*- coding: utf-8 -*-
# author: boe

from flask import Blueprint
from flask_restful import Api

from app.tax_audit.analys_views import (TaxAmountAnalysisExport,
                                        TaxAmountAnalysisList)
from app.tax_audit.confiscate_views import TaxPenaltyExport, TaxPenaltyList
from app.tax_audit.detail_views import (TaxDoubtsDetail, TaxDoubtsExport,
                                        TaxDoubtsList)
from app.tax_audit.import_views import TaskCheck, TaxExcelImport
from app.tax_audit.record_views import TaxRecordList


tax = Blueprint("tax", __name__)
_api = Api(tax)

_api.add_resource(TaxExcelImport, "/tax/records/import")
_api.add_resource(TaskCheck, "/tax/task-result")
_api.add_resource(TaxDoubtsList, "/tax/doubts", "/tax/doubts/history")
_api.add_resource(TaxDoubtsDetail, "/tax/doubts/<string:id>")
_api.add_resource(TaxDoubtsExport, "/tax/doubts/export")

_api.add_resource(TaxAmountAnalysisList, "/tax/ents-analys/amount")
_api.add_resource(TaxAmountAnalysisExport, "/tax/ents-analys/export-amount")

_api.add_resource(TaxPenaltyList, "/tax/ents-analys/penalty")
_api.add_resource(TaxPenaltyExport, "/tax/ents-analys/export-penalty")

_api.add_resource(TaxRecordList, "/tax/records")
