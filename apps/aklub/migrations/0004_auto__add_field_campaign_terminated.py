# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Campaign.terminated'
        db.add_column(u'aklub_campaign', 'terminated',
                      self.gf('django.db.models.fields.DateField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Campaign.acquisition_campaign'
        db.add_column(u'aklub_campaign', 'acquisition_campaign',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Campaign.real_yield'
        db.add_column(u'aklub_campaign', 'real_yield',
                      self.gf('django.db.models.fields.FloatField')(null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Campaign.terminated'
        db.delete_column(u'aklub_campaign', 'terminated')

        # Deleting field 'Campaign.acquisition_campaign'
        db.delete_column(u'aklub_campaign', 'acquisition_campaign')

        # Deleting field 'Campaign.real_yield'
        db.delete_column(u'aklub_campaign', 'real_yield')


    models = {
        u'aklub.accountstatements': {
            'Meta': {'ordering': "['-import_date']", 'object_name': 'AccountStatements'},
            'csv_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'date_from': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_to': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2013, 7, 16, 0, 0)'})
        },
        u'aklub.automaticcommunication': {
            'Meta': {'object_name': 'AutomaticCommunication'},
            'condition': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['aklub.Condition']"}),
            'dispatch_auto': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'only_once': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'sent_to_users': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['aklub.User']", 'symmetrical': 'False', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'subject_en': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'template': ('django.db.models.fields.TextField', [], {'max_length': '10000'}),
            'template_en': ('django.db.models.fields.TextField', [], {'max_length': '10000', 'null': 'True', 'blank': 'True'})
        },
        u'aklub.campaign': {
            'Meta': {'object_name': 'Campaign'},
            'acquisition_campaign': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '3000', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'real_yield': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'terminated': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'})
        },
        u'aklub.communication': {
            'Meta': {'ordering': "['date']", 'object_name': 'Communication'},
            'attachment': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'created_by_communication'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'dispatched': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'handled_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'handled_by_communication'", 'null': 'True', 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'note': ('django.db.models.fields.TextField', [], {'max_length': '3000', 'blank': 'True'}),
            'send': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'summary': ('django.db.models.fields.TextField', [], {'max_length': '10000'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'individual'", 'max_length': '30'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['aklub.User']"})
        },
        u'aklub.condition': {
            'Meta': {'object_name': 'Condition'},
            'as_filter': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'conds': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'conds_rel'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['aklub.Condition']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'operation': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'variable': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'})
        },
        u'aklub.expense': {
            'Meta': {'object_name': 'Expense'},
            'amount': ('django.db.models.fields.FloatField', [], {}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'expenses'", 'to': u"orm['aklub.Campaign']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'})
        },
        u'aklub.masscommunication': {
            'Meta': {'object_name': 'MassCommunication'},
            'attach_tax_confirmation': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'attachment': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'send_to_users': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['aklub.User']", 'symmetrical': 'False', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'subject_en': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'template': ('django.db.models.fields.TextField', [], {'max_length': '10000', 'null': 'True', 'blank': 'True'}),
            'template_en': ('django.db.models.fields.TextField', [], {'max_length': '10000', 'null': 'True', 'blank': 'True'})
        },
        u'aklub.payment': {
            'KS': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'Meta': {'ordering': "['-date']", 'object_name': 'Payment'},
            'SS': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'VS': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'account': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'account_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'account_statement': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['aklub.AccountStatements']", 'null': 'True', 'blank': 'True'}),
            'amount': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'bank_code': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'bank_name': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'done_by': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['aklub.User']", 'null': 'True', 'blank': 'True'}),
            'user_identification': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'})
        },
        u'aklub.recruiter': {
            'Meta': {'object_name': 'Recruiter'},
            'campaigns': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['aklub.Campaign']", 'symmetrical': 'False', 'blank': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'firstname': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'max_length': '3000', 'blank': 'True'}),
            'problem': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'rating': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'recruiter_id': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True'}),
            'registered': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2013, 7, 16, 0, 0)'}),
            'surname': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'telephone': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'})
        },
        u'aklub.statmembercountsbymonths': {
            'Meta': {'object_name': 'StatMemberCountsByMonths', 'db_table': "'aklub_v_member_counts_by_months'", 'managed': 'False'},
            'id': ('django.db.models.fields.CharField', [], {'max_length': '20', 'primary_key': 'True'}),
            'irregular': ('django.db.models.fields.IntegerField', [], {}),
            'month': ('django.db.models.fields.IntegerField', [], {}),
            'regular': ('django.db.models.fields.IntegerField', [], {}),
            'run_total': ('django.db.models.fields.IntegerField', [], {}),
            'total': ('django.db.models.fields.IntegerField', [], {}),
            'year': ('django.db.models.fields.IntegerField', [], {})
        },
        u'aklub.statpaymentsbymonths': {
            'Meta': {'object_name': 'StatPaymentsByMonths', 'db_table': "'aklub_v_payments_by_months'", 'managed': 'False'},
            'donors': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '20', 'primary_key': 'True'}),
            'month': ('django.db.models.fields.IntegerField', [], {}),
            'run_total': ('django.db.models.fields.IntegerField', [], {}),
            'total': ('django.db.models.fields.IntegerField', [], {}),
            'year': ('django.db.models.fields.IntegerField', [], {})
        },
        u'aklub.taxconfirmation': {
            'Meta': {'unique_together': "(('user', 'year'),)", 'object_name': 'TaxConfirmation'},
            'amount': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['aklub.User']"}),
            'year': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'aklub.user': {
            'Meta': {'object_name': 'User'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'additional_information': ('django.db.models.fields.TextField', [], {'max_length': '500', 'blank': 'True'}),
            'addressment': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'addressment_on_envelope': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'campaigns': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['aklub.Campaign']", 'symmetrical': 'False', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'club_card_available': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'club_card_dispatched': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'country': ('django.db.models.fields.CharField', [], {'default': "u'\\u010cesk\\xe1 republika'", 'max_length': '40', 'blank': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'exceptional_membership': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'expected_date_of_first_payment': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'field_of_work': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'firstname': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'knows_us_from': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'cs'", 'max_length': '50'}),
            'note': ('django.db.models.fields.TextField', [], {'max_length': '2000', 'blank': 'True'}),
            'other_benefits': ('django.db.models.fields.TextField', [], {'max_length': '500', 'blank': 'True'}),
            'other_support': ('django.db.models.fields.TextField', [], {'max_length': '500', 'blank': 'True'}),
            'profile_picture': ('stdimage.fields.StdImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'profile_text': ('django.db.models.fields.TextField', [], {'max_length': '3000', 'null': 'True', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'recruiter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['aklub.Recruiter']", 'null': 'True', 'blank': 'True'}),
            'registered_support': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 7, 16, 0, 0)', 'blank': 'True'}),
            'regular_amount': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'regular_frequency': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'regular_payments': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sex': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'street': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'surname': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'telephone': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'title_after': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'title_before': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'variable_symbol': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '30'}),
            'verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'verified_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'verified_users'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'why_supports': ('django.db.models.fields.TextField', [], {'max_length': '500', 'blank': 'True'}),
            'wished_information': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'wished_tax_confirmation': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'wished_welcome_letter': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'zip_code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['aklub']