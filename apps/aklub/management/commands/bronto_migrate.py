#!/usr/bin/env python
import json
from aklub.models import (
    AdministrativeUnit,
    ProfileEmail,
    UserProfile,
    Telephone,
    Profile,
    BankAccount,
)
from events.models import (
    Event,
    EventType,
    Location,
    OrganizationPosition,
    OrganizationTeam,
)
from interactions.models import InteractionCategory, InteractionType, Interaction
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.utils import timezone

try:
    import mysql.connector
except ImportError:
    print("Import error, please run\n pip install mysql-connector-python-rf")


class Command(BaseCommand):
    help = """ creates superuser account and account under
               administrative unit (development purpose)
           """  # noqa

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "--dbpassword",
            dest="dbpassword",
            default=None,
            type=str,
            help="Specifies the password for the mysql db that you're migrating from.",
        )
        parser.add_argument(
            "--dbhost",
            dest="dbhost",
            default=None,
            type=str,
            help="Specifies the hostname for the mysql db that you're migrating from.",
        )
        parser.add_argument(
            "--dbuser",
            dest="dbuser",
            default=None,
            type=str,
            help="Specifies the user for the mysql db that you're migrating from.",
        )
        parser.add_argument(
            "--db",
            dest="db",
            default=None,
            type=str,
            help="Specifies the db for the mysql db that you're migrating from.",
        )
        parser.add_argument(
            "--dont-export-users",
            dest="dont_export_users",
            default=False,
            help="Export users?",
            action="store_true",
        )

    def handle(self, *args, **options):
        mydb = mysql.connector.connect(
            host=options.get("dbhost"),
            user=options.get("dbuser"),
            password=options.get("dbpassword"),
            database=options.get("db"),
        )
        cur = mydb.cursor(buffered=True, dictionary=True)
        if not options.get("dont_export_users"):
            print("------------------ migrace uzivatelu----------------------")
            cur = mydb.cursor(buffered=True, dictionary=True)
            sql = "SELECT * from adresa"
            cur.execute(sql)
            adresa_all = cur.fetchall()
            dups = []
            exceptions = open("user-exceptions", "w")
            for adresa in adresa_all:
                try:
                    user, created = UserProfile.objects.get_or_create(
                        id=adresa["id"],
                        username=adresa["id"],
                        defaults={
                            "title_before": adresa.get("titul"),
                            "nickname": adresa.get("prezdivka") or "",
                            "first_name": adresa.get("jmeno"),
                            "last_name": adresa.get("prijmeni"),
                            "addressment": adresa.get("osloveni") or "",
                            "maiden_name": adresa.get("rodne_prijmeni") or "",
                            "street": adresa.get("ulice") or "",
                            "city": adresa.get("mesto") or "",
                            "zip_code": adresa.get("psc") or "",
                            "age_group": adresa.get("datum_narozeni").year
                            if adresa.get("datum_narozeni")
                            else None,
                            "birth_month": adresa.get("datum_narozeni").month
                            if adresa.get("datum_narozeni")
                            else None,
                            "birth_day": adresa.get("datum_narozeni").day
                            if adresa.get("datum_narozeni")
                            else None,
                            "correspondence_street": adresa.get("kont_ulice") or "",
                            "correspondence_city": adresa.get("kont_mesto") or "",
                            "correspondence_zip_code": adresa.get("kont_psc") or "",
                            "note": adresa.get("poznamka") or "",
                            "created": adresa.get("created_at"),
                        },
                    )
                except Exception as e:
                    print(adresa, "field to long exception.", str(e))
                    exceptions.write(str(adresa) + "\n")

                try:
                    pe = ProfileEmail.objects.get(email=adresa["email"])
                    if pe.user != user:
                        print(adresa.get("email"), "probably duplicited", adresa)
                        d = pe.user.__dict__
                        del d["_state"]
                        del d["created"]
                        del d["updated"]
                        del d["date_joined"]
                        del d["profile_picture"]
                        print(d)
                        dups.append(adresa)
                        dups.append(d)
                except ProfileEmail.DoesNotExist:
                    pass

                if created:
                    # print("User ", adresa.get("jmeno"), " added.")
                    if adresa.get("email"):
                        try:
                            email = ProfileEmail.objects.create(
                                user=user, email=adresa["email"], is_primary=True
                            )
                        except Exception as e:
                            pass

                    if adresa.get("telefon"):
                        Telephone.objects.create(
                            is_primary=True, user=user, telephone=adresa.get("telefon")
                        )

            import csv

            keys = set(dups[0].keys())
            keys.update(dups[1].keys())
            with open("user-dups.csv", "w", newline="") as output_file:
                dict_writer = csv.DictWriter(output_file, keys)
                dict_writer.writeheader()
                dict_writer.writerows(dups)
            exceptions.close()
        print("------------------ migrace administrativeu units----------------------")
        cur = mydb.cursor(buffered=True, dictionary=True)
        sql = "SELECT * from klub"
        cur.execute(sql)
        au_all = cur.fetchall()
        for au in au_all:
            uroven = au.get("uroven")
            if uroven == 1:
                uroven = "club"
            elif uroven == 2:
                uroven = "basic_section"
            elif uroven == 3:
                uroven = "regional_center"
            elif uroven == 4:
                uroven = "headquarter"

            try:
                president = UserProfile.objects.get(id=au.get("predseda"))
            except UserProfile.DoesNotExist:
                print(
                    "Could not find president (id = {}) for AdministrativeUnit {}".format(
                        au.get("predseda"), au
                    )
                )

            AdministrativeUnit.objects.get_or_create(
                id=au.get("id") or "",
                defaults={
                    "name": au.get("nazev") or "",
                    "street": au.get("ulice") or "",
                    "city": au.get("mesto") or "",
                    "zip_code": au.get("zip_code") or "",
                    "web_url": au.get("www"),
                    "level": uroven,
                    "telephone": au.get("telefon") or "",
                    "from_email_address": au.get("email") or "",
                    "president": president,
                    "president_since": au.get("predseda_od"),
                },
            )

        print("--------- Loading zakladní članky --------------")
        sql = "SELECT * from zc"
        cur.execute(sql)
        zc_all = cur.fetchall()
        for zc in zc_all:
            au = AdministrativeUnit.objects.get(id=zc.get("id"))
            au.ico = zc.get("ic")
            try:
                au.manager = UserProfile.objects.get(id=zc.get("hospodar"))
            except UserProfile.DoesNotExist:
                print("No manager for au ", au, zc)
            au.manager_since = zc.get("hospodar_od")
            try:
                au.president = UserProfile.objects.get(id=zc.get("statutar"))
            except UserProfile.DoesNotExist:
                print("No president for au ", au, zc)
            au.president_since = zc.get("statutar_od")
            try:
                au.vice_president = UserProfile.objects.get(id=zc.get("statutar2"))
            except UserProfile.DoesNotExist:
                print("No vice president for au ", au, zc)
            au.vice_president_since = zc.get("statutar2_od")
            acct_number = zc.get("ucet", "")
            if acct_number:
                BankAccount.objects.get_or_create(
                    bank_account_number=acct_number,
                    administrative_unit=au,
                )

        sql = "SELECT * from akce_typ"
        cur.execute(sql)
        au_nezname, _ = AdministrativeUnit.objects.get_or_create(
            id=AdministrativeUnit.objects.order_by("-id").first().id + 1,
            name="neznámý",
        )
        print("------------------ migrace event_typ----------------------")
        sql = "SELECT * from akce_typ"
        cur.execute(sql)
        event_type_all = cur.fetchall()
        for administrative_unit in AdministrativeUnit.objects.all():
            for event_type in event_type_all:
                EventType.objects.get_or_create(
                    name=event_type.get("nazev"),
                    slug=event_type.get("kod"),
                    administrative_unit=administrative_unit,
                )
        print("------ importování lokalit ------")
        sql = "SELECT * from lokalita"
        cur.execute(sql)
        lokalita_all = cur.fetchall()
        for lokalita in lokalita_all:
            location, _ = Location.objects.get_or_create(
                pk=lokalita.get("id"),
            )
            location.name = lokalita.get("nazev")
            location.place = lokalita.get("misto")
            regions = {
                None: "Neznámé",
                0: "Neznámé",
                1: "Praha",
                2: "Středočeský",
                3: "Ústecký",
                4: "Liberecký",
                5: "Pardubický",
                6: "Královéhradecký",
                7: "Jihočeský",
                8: "Plzeňský",
                9: "Karlovarský",
                10: "Vysočina",
                11: "Jihomoravský",
                12: "Olomoucký",
                13: "Moavskoslezský",
                14: "Zlínský",
                15: "Zahraničí",
            }
            location.region = regions[lokalita.get("kraj")]

        print("------------------ migrace eventu----------------------")
        sql = "SELECT * from akce"
        cur.execute(sql)
        akce_all = cur.fetchall()
        for akce in akce_all:
            # program
            program = akce.get("program")
            if program == 1:
                program = "nature"
            elif program == 2:
                program = "monuments"
            elif program == 3:
                program = "PsB"
            elif program == 4:
                program = "children_section"
            elif program == 5:
                program = "eco_consulting"
            elif program == 6:
                program = "education"
            else:
                program = ""

            indended_for = akce.get("prokoho")
            if indended_for == 1:
                indended_for = "everyone"
            elif indended_for == 2:
                indended_for = "adolescents_and_adults"
            elif indended_for == 3:
                indended_for = "children"
            elif indended_for == 4:
                indended_for = "parents_and_children"
            elif indended_for == 5:
                indended_for = "newcomers"

            grant = akce.get("dotace")
            if grant == 0:
                grant = "no_grant"
            elif grant == 1:
                grant = "MEYS"
            elif grant == 2:
                grant = "others"

            prihlaska = akce.get("prihlaska")
            if prihlaska == 1:
                prihlaska = "standard"
            elif prihlaska == 2:
                prihlaska = "by_email"
            elif prihlaska == 3:
                prihlaska = "other_electronic"
            elif prihlaska == 4:
                prihlaska = "not_required"
            elif prihlaska == 5:
                prihlaska = "full"
            Event.objects.get_or_create(
                id=akce.get("id"),
                name=akce.get("nazev"),
                date_from=akce.get("od"),
                date_to=akce.get("do"),
                defaults={
                    "number_of_actions": akce.get("pocet"),
                    "is_internal": akce.get("klubova") if akce.get("klubova") else 0,
                    "basic_purpose": "action-with-attendee-list"
                    if akce.get("adresar", False)
                    else "action",
                    "program": program,
                    "indended_for": indended_for,
                    "age_from": akce.get("vek_od"),
                    "age_to": akce.get("vek_do"),
                    "hours_worked": akce.get("odpracovano"),
                    "note": akce.get("poznamka") or "",
                    "additional_question_1": akce.get("add_info_title") or "",
                    "additional_question_2": akce.get("add_info_title_2") or "",
                    "additional_question_3": akce.get("add_info_title_3") or "",
                    "total_participants": akce.get("lidi"),
                    "total_participants_under_26": akce.get("lidi_do26"),
                    "public_on_web": akce.get("zverejnit"),
                    "registration_method": prihlaska,
                    "participation_fee": akce.get("poplatek") or "",
                    "looking_forward_to_you": akce.get("org") or "",
                    "entry_form_url": akce.get("kontakt_url"),
                    "web_url": akce.get("web"),
                    "invitation_text_short": akce.get("text") or "",
                    "invitation_text_1": akce.get("text_uvod") or "",
                    "invitation_text_2": akce.get("text_info") or "",
                    "invitation_text_3": akce.get("text_dobr") or "",
                    "invitation_text_4": akce.get("text_mnam") or "",
                    "grant": grant,
                    "focus_on_members": akce.get("zamereno_na_cleny"),
                    "additional_photo_1": akce.get("priloha_1"),
                    "additional_photo_2": akce.get("priloha_2"),
                    "additional_photo_3": akce.get("priloha_3"),
                    "additional_photo_4": akce.get("priloha_4"),
                    "additional_photo_5": akce.get("priloha_5"),
                    "additional_photo_6": akce.get("priloha_6"),
                    "contact_person_name": akce.get("kontakt") or "",
                    "contact_person_telephone": akce.get("kontakt_telefon") or "",
                    "contact_person_email": akce.get("kontakt_email") or "",
                },
            )

        print("------ nahravání taborů ------")
        sql = "SELECT * from tabor"
        cur.execute(sql)
        tabor_all = cur.fetchall()
        for tabor in tabor_all:
            event = Event.objects.get(id=tabor.get("id"))
            event.basic_purpose = "camp"
            event.working_hours = tabor.get("pracovni_doba")
            event.total_working_days = tabor.get("pracovni_dny")
            event.accommodation = tabor.get("ubytovani")
            if event.accommodation is None:
                event.accommodation = ""
            diets = {
                0: ["vegetarian", "non_vegetarian"],
                1: ["vegetarian"],
                2: ["non_vegetarian"],
                3: [],
                None: [],
            }
            event.diet = diets[tabor.get("strava")]
            event.vip_action = tabor.get("vip") == 1
            event.promoted_in_magazine = tabor.get("rover") == 1
            event.save()

        print("------ prirazovani administrativnich jednotek k eventum------")

        sql = "SELECT * from porada"
        cur.execute(sql)
        porada_all = cur.fetchall()
        for porada in porada_all:
            try:
                event = Event.objects.get(id=porada.get("akce"))
            except:
                print(porada, "event neexistuje")
            try:
                unit = AdministrativeUnit.objects.get(id=porada.get("klub"))
            except:
                print(porada, "unit neexistuje")
            event.administrative_units.add(unit)

        print(
            "a taky jejich event_type (takze znova to projedem pač už víme jaké administrativni jednotky eventy maji)"
        )
        sql = "SELECT akce.id, typ, kod, akce_typ.nazev from akce join akce_typ on akce.typ=akce_typ.id;"
        cur.execute(sql)
        akce_all = cur.fetchall()
        for akce in akce_all:
            event = Event.objects.get(id=akce.get("id"))
            if not event.administrative_units.all().exists():
                event.administrative_units.add(au_nezname)
            print(akce)
            event_types = EventType.objects.filter(
                name=akce.get("nazev"),
                administrative_unit=event.administrative_units.first(),
            )
            print(event_types)

            event.event_type = event_types.first()
            event.save()

        print("------ prirazovani ucastníků k akcím k eventum------")
        sql = "SELECT * from ucastnik"
        cur.execute(sql)
        ucastnik_all = cur.fetchall()
        cat, _ = InteractionCategory.objects.get_or_create(
            category="Účast na akci",
            display=True,
        )

        type, _ = InteractionType.objects.get_or_create(
            name="Účast na akci",
            category=cat,
        )
        org_pos, _ = OrganizationPosition.objects.get_or_create(
            name="Organizátor (nespecifikováno)"
        )
        for ucastnik in ucastnik_all:
            try:
                event = Event.objects.get(id=ucastnik.get("akce"))
            except:
                print(ucastnik, "event neexistuje")
                continue
            try:
                user = UserProfile.objects.get(id=ucastnik.get("adresa"))
            except:
                print(ucastnik, "user neexistuje")
                continue
            Interaction.objects.create(
                event=event,
                subject="Účast na akci",
                administrative_unit=event.administrative_units.first()
                if event.administrative_units.first()
                else au_nezname,
                user=user,
                type=type,
                date_from=event.date_from if event.date_from else timezone.now(),
            )
            if ucastnik.get("org") == 1:
                OrganizationTeam.objects.get_or_create(
                    profile=user,
                    event=event,
                    position=org_pos,
                )

            if event.administrative_units.all().exists():
                user.administrative_units.add(*event.administrative_units.all())

        print("------ prirazení členství TYPY------")

        sql = "SELECT * from clen_typ"
        cur.execute(sql)
        clen_typ_all = cur.fetchall()

        cat, _ = InteractionCategory.objects.get_or_create(
            category="Členství v Brontosaurech",
            display=True,
        )
        for typ in clen_typ_all:
            inttype, _ = InteractionType.objects.get_or_create(
                name=typ.get("nazev"),
                category=cat,
                slug=typ.get("kod"),
                date_to_bool=True,
            )
        print("------ prirazení členství------")
        posrana_mapa = {
            1: "i",
            2: "r",
            3: "rp",
            4: "d",
            5: "x",
            6: "im",
        }
        sql = "SELECT * from clen"
        cur.execute(sql)
        clen_all = cur.fetchall()
        for clen in clen_all:
            if clen.get("karta"):
                cislo_karty = f'Číslo karty: {clen["karta"]}'
            else:
                cislo_karty = ""
            try:
                au = AdministrativeUnit.objects.get(id=clen["klub"])
            except:
                print("AU does not exist... skipping", clen)
            try:
                user = UserProfile.objects.get(id=clen["adresa"])
            except:
                print("User does not exist... skipping", clen)
                continue
            Interaction.objects.get_or_create(
                subject="Členství v Brontosaurech",
                administrative_unit=au,
                user=user,
                type=InteractionType.objects.get(slug=posrana_mapa[clen["typ"]]),
                date_from=clen["od"] if clen.get("od") else clen.get("do"),
                date_to=clen["do"],
                note=cislo_karty,
            )
