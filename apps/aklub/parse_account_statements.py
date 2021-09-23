import codecs
import csv
import datetime

from django.utils.translation import ugettext_lazy as _

from . import models


def str_to_datetime(date):
    if not date:
        return None
    return datetime.date(
        **dict(
            zip(
                ["day", "month", "year"],
                [int(val) for val in date.split(".")],
            ),
        ),
    )


def register_payment(p_sort, self):
    p = models.Payment.objects.create(**p_sort)
    models.AccountStatements.payment_pair(self, p)
    p.type = "bank-transfer"
    p.account_statement = self
    return p


def amount_to_int(amount):
    return int(round(float(amount.replace(",", ".").replace(" ", ""))))


def check_incomming(amount):
    return amount < 0


def header_parse(
    payments_reader,
    date_from_name,
    date_to_name,
    recipient_account_name=None,
    statement=None,
):
    for payment in payments_reader:
        if payment[payments_reader.fieldnames[0]] == recipient_account_name:

            account = payment[payments_reader.fieldnames[1]]
            if "CZK" in account:  # because KB statement has CZK in account name
                account = account.split()[0]
            try:
                recipient_account = models.BankAccount.objects.get(
                    bank_account_number__contains=account
                )
            except models.BankAccount.DoesNotExist:
                statement.pair_log = _(
                    "Missing Bank account: %(acc)s, add it in BankAccounts"
                ) % {"acc": account}
                raise
            else:
                statement.pair_log = ""

        if payment[payments_reader.fieldnames[0]] == date_from_name:
            date_from = payment[payments_reader.fieldnames[1]]

        if payment[payments_reader.fieldnames[0]] == date_to_name:
            date_to = payment[payments_reader.fieldnames[1]]
            if (
                date_to != ""
            ):  # because of kb statement has two empty rows and the second one is date
                break
    return date_from, date_to, recipient_account


def date_format(date):
    if not date:
        return None
    else:
        date = date.split("/")
        return date[0] + "-" + date[1] + "-" + date[2]


def delete_left_nulls(number):
    number = int(number)
    if number == 0:
        return ""
    return str(number)


def get_four_digit(code):
    if code:
        return "%0*d" % (4, int(code))
    else:
        return code


class ParseAccountStatement(object):
    def parse_bank_csv_fio(self):
        payments_reader = csv.DictReader(
            codecs.iterdecode(self.csv_file, "utf-8"),
            delimiter=";",
            fieldnames=[
                "operation_id",
                "date",
                "amount",
                "currency",
                "account",
                "account_name",
                "bank_code",
                "bank_name",
                "KS",
                "VS",
                "SS",
                "user_identification",
                "recipient_message",
                "transfer_type",
                "done_by",
                "specification",
                "transfer_note",
                "BIC",
                "order_id",
            ],
        )
        date_from, date_to, recipient_account = header_parse(
            payments_reader=payments_reader,
            date_from_name="dateStart",
            date_to_name="dateEnd",
            recipient_account_name='\ufeff"accountId"',
            statement=self,
        )
        self.date_from = str_to_datetime(date_from)
        self.date_to = str_to_datetime(date_to)
        csv_head = True
        payments = []
        for payment in payments_reader:
            if csv_head:
                if payment[payments_reader.fieldnames[0]] == "ID operace":
                    csv_head = False
            else:

                payment["date"] = str_to_datetime(payment["date"])
                payment["amount"] = amount_to_int(payment["amount"])
                payment["bank_code"] = get_four_digit(payment["bank_code"])
                payment["recipient_account"] = recipient_account
                if check_incomming(payment["amount"]):
                    continue
                payments.append(register_payment(payment, self))
        return payments

    def parse_bank_csv_cs(self):
        payments_reader = csv.DictReader(
            codecs.iterdecode(self.csv_file, "cp1250"),
            delimiter=";",
            fieldnames=[
                "predcisli_uctu",
                "cislo_uctu",
                "kod_banky",
                "castka",
                "prichozi/odchozi",
                "ucetni/neucetni",
                "KS",
                "SS",
                "popis_transakce",
                "nazev_protiucet",
                "bank_reference",
                "zprava_prijemce",
                "zprava_platce",
                "datum_valuta",
                "datum_zpracovani",
                "VS1",
                "VS2",
                "reference_platby",
                "duvod_neprovedeni",
            ],
        )
        date_from, date_to, recipient_account = header_parse(
            payments_reader=payments_reader,
            date_from_name="Počáteční datum období",
            date_to_name="Konečné datum období",
            recipient_account_name="Číslo účtu",
            statement=self,
        )
        self.date_from = date_format(date_from)
        self.date_to = date_format(date_to)
        csv_head = True
        payments = []
        for payment in payments_reader:
            if csv_head:
                if (
                    payment[payments_reader.fieldnames[0]]
                    == "Předčíslí účtu plátce/příjemce"
                ):
                    csv_head = False
            else:
                if not payment["predcisli_uctu"]:
                    account = payment["cislo_uctu"]
                else:
                    account = payment["predcisli_uctu"] + "-" + payment["cislo_uctu"]
                p_sort = {
                    "account": account,
                    "bank_code": get_four_digit(payment["kod_banky"]),
                    "KS": payment["KS"],
                    "SS": payment["SS"],
                    "amount": payment["castka"],
                    "account_name": payment["nazev_protiucet"],
                    "recipient_message": payment["zprava_prijemce"],
                    "transfer_note": payment["zprava_platce"],
                    "date": payment["datum_valuta"],
                    "VS": payment["VS1"],
                    "VS2": payment["VS2"],
                    "operation_id": payment["bank_reference"],
                    "recipient_account": recipient_account,
                }
                p_sort["date"] = date_format(p_sort["date"])
                p_sort["amount"] = amount_to_int(p_sort["amount"])

                if check_incomming(p_sort["amount"]):
                    continue
                payments.append(register_payment(p_sort, self))

        return payments

    def parse_bank_csv_kb(self):
        payments_reader = csv.DictReader(
            codecs.iterdecode(self.csv_file, "cp1250"),
            delimiter=";",
            fieldnames=[
                "Datum splatnosti",
                "Datum odepsani z jine banky",
                "Protiucet/Kod banky",
                "Nazev protiuctu",
                "Castka",
                "Originalni castka",
                "Originalni mena",
                "Kurz",
                "VS",
                "KS",
                "SS",
                "Identifikace transakce",
                "Systemovy popis",
                "Popis prikazce",
                "Popis pro prijemce",
                "AV pole 1",
                "AV pole 2",
                "AV pole 3",
                "AV pole 4",
            ],
        )
        date_from, date_to, recipient_account = header_parse(
            payments_reader=payments_reader,
            date_from_name="Vypis za obdobi",
            date_to_name="",
            recipient_account_name="Cislo uctu",
            statement=self,
        )

        self.date_from = str_to_datetime(date_from)
        self.date_to = str_to_datetime(date_to)

        csv_head = True
        payments = []
        for payment in payments_reader:
            if csv_head:
                if payment[payments_reader.fieldnames[0]] == "Datum splatnosti":
                    csv_head = False
            else:
                p_sort = {
                    "account": payment["Protiucet/Kod banky"].split("/")[0],
                    "bank_code": get_four_digit(
                        payment["Protiucet/Kod banky"].split("/")[1]
                    ),
                    "VS": payment["VS"],
                    "KS": payment["KS"],
                    "SS": payment["SS"],
                    "amount": payment["Castka"],
                    "account_name": payment["Nazev protiuctu"],
                    "recipient_message": payment["Popis pro prijemce"],
                    "transfer_note": payment["AV pole 1"].replace(" ", "")
                    + ", "
                    + payment["AV pole 2"].replace(" ", ""),
                    "date": payment["Datum splatnosti"],
                    "recipient_account": recipient_account,
                }
                p_sort["amount"] = amount_to_int(p_sort["amount"])
                p_sort["date"] = str_to_datetime(p_sort["date"])

                if check_incomming(p_sort["amount"]):
                    continue
                payments.append(register_payment(p_sort, self))
        return payments

    def parse_bank_csv_csob(self):
        payments_reader = csv.DictReader(
            codecs.iterdecode(self.csv_file, "cp1250"),
            delimiter=";",
            fieldnames=[
                "cislo uctu",
                "mena1",
                "alias",
                "nazev uctu",
                "datum zauctovani",
                "datum valuty",
                "castka",
                "mena2",
                "zustatek",
                "konstantni symbol",
                "variabilni symbol",
                "specificky symbol",
                "popis",
                "protistrana",
                "ucet protistrany",
                "zprava prijemci i platci",
                "identifikace",
                "castka platby",
                "mena platby",
                "poznamka",
                "nazev 3. strany",
                "identifikator 3. strany",
            ],
        )
        csv_head = True
        payments = []
        for payment in payments_reader:
            if csv_head:
                line_parse = payment[payments_reader.fieldnames[0]].split(" ")
                if payment[payments_reader.fieldnames[0]] == "číslo účtu":
                    csv_head = False
                elif line_parse[0] == "Datum":
                    self.date_from = str_to_datetime(line_parse[4])
                    self.date_to = str_to_datetime(line_parse[7].replace(";", ""))
                elif line_parse[0] == "CEB":
                    account = line_parse[12].replace(";", "")
                    try:
                        recipient_account = models.BankAccount.objects.get(
                            bank_account_number__contains=account
                        )
                    except models.BankAccount.DoesNotExist:
                        self.pair_log = "Missing Bank account, add it in BankAccounts"
            else:
                p_sort = {
                    "account": payment["ucet protistrany"].split("/")[0],
                    "bank_code": get_four_digit(
                        payment["ucet protistrany"].split("/")[1]
                    ),
                    "VS": payment["variabilni symbol"],
                    "KS": payment["konstantni symbol"],
                    "SS": payment["specificky symbol"],
                    "amount": payment["castka"],
                    "currency": payment["mena2"],
                    "account_name": payment["protistrana"],
                    "recipient_message": payment["zprava prijemci i platci"],
                    "transfer_note": payment["poznamka"],
                    "date": payment["datum zauctovani"],
                    "recipient_account": recipient_account,
                }

                p_sort["amount"] = amount_to_int(p_sort["amount"])
                p_sort["date"] = str_to_datetime(p_sort["date"])

                if check_incomming(p_sort["amount"]):
                    continue
                payments.append(register_payment(p_sort, self))
        return payments

    def parse_bank_csv_sberbank(self):
        payments_reader = csv.DictReader(
            codecs.iterdecode(self.csv_file, "cp1250"),
            delimiter="	",
            fieldnames=[
                "owner_bank_number",
                "currency1",
                "transfer_type",
                "date1",
                "date2",
                "incomming_outcomming",
                "amount",
                "currency2",
                "bank_account",
                "bank_code",
                "account_name",
                "symbols",
                "message",
            ],
        )
        payments = []
        recipient_account = None
        for payment in payments_reader:
            if not recipient_account:
                try:
                    recipient_account = models.BankAccount.objects.get(
                        bank_account_number__contains=payment[
                            "owner_bank_number"
                        ].split()[1],
                    )
                except models.BankAccount.DoesNotExist:
                    self.pair_log = "Missing Bank account, add it in BankAccounts"

            if payment["incomming_outcomming"] != "Příchozí platba":
                continue

            VS, KS, SS = payment["symbols"].split(",")

            p_sort = {
                "account": delete_left_nulls(payment["bank_account"]),
                "bank_code": get_four_digit(payment["bank_code"]),
                "VS": delete_left_nulls(VS),
                "KS": delete_left_nulls(KS),
                "SS": delete_left_nulls(SS),
                "amount": amount_to_int(payment["amount"]),
                "currency": payment["currency2"],
                "account_name": payment["account_name"],
                "recipient_message": payment["message"],
                "date": str_to_datetime(payment["date1"]),
                "transfer_type": payment["transfer_type"],
                "recipient_account": recipient_account,
            }

            payments.append(register_payment(p_sort, self))
        return payments

    def parse_bank_csv_raiffeisenbank(self):
        payments_reader = csv.DictReader(
            codecs.iterdecode(self.csv_file, "cp1250"),
            delimiter=";",
            fieldnames=[
                "datum_provedeni",
                "datum_zauctovani",
                "cislo_uctu",
                "nazev_uctu",
                "kategorie_transakce",
                "cislo_protiuctu",
                "nazev_protiuctu",
                "typ_transakce",
                "zprava",
                "poznamka",
                "VS",
                "KS",
                "SS",
                "zauctovana_castka",
                "mena_uctu",
                "puvodni_castka_a_mena",
                "puvodni_castka_a_mena_2",
                "poplatek",
                "id_transakce",
                "vlastni_poznamka",
                "nazev_obchodnika",
                "mesto",
            ],
        )
        payments = []
        recipient_account = None
        for payment in payments_reader:
            if payment[payments_reader.fieldnames[0]] == "Datum provedení":
                continue

            if check_incomming(amount_to_int(payment["zauctovana_castka"])):
                continue

            if not recipient_account:
                try:
                    recipient_account = models.BankAccount.objects.get(
                        bank_account_number=payment["cislo_uctu"],
                    )
                except models.BankAccount.DoesNotExist:
                    self.pair_log = "Missing Bank account, add it in BankAccounts"

            account = payment["cislo_protiuctu"].split("/")
            p_sort = {
                "account": account[0],
                "bank_code": account[1] if len(account) > 1 else "",
                "VS": payment["VS"],
                "KS": payment["KS"],
                "SS": payment["SS"],
                "amount": amount_to_int(payment["zauctovana_castka"]),
                "currency": payment["mena_uctu"],
                "account_name": payment["nazev_protiuctu"],
                "recipient_message": payment["zprava"],
                "transfer_note": payment["poznamka"],
                "date": str_to_datetime(payment["datum_zauctovani"].split(" ")[0]),
                "recipient_account": recipient_account,
                "operation_id": payment["id_transakce"],
            }
            payments.append(register_payment(p_sort, self))
        return payments
