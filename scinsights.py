# Python-wrapped REST API utilities for AppResponse 11

import os
import sys
import requests
import time
import argparse
import json
import xlsxwriter

from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Avoid warnings for insecure certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

import types

SCINSIGHTS_REPORT_WAIT = 5
SCINSIGHTS_OUTPUT_FILE = "InsightsSiteSummary.xlsx"
SCINSIGHTS_OUTPUT_HEADER_HEIGHT = 45
SCINSIGHTS_OUTPUT_COLUMN_SPACING = 14

SCINSIGHTS_UTILITIES_ACTIONS = ["site_summary"]

SCINSIGHTS_TOPTALKERS_UPLINK_DATADEF_INDEX = 0
SCINSIGHTS_TOPTALKERS_UPLINK_ID_COLUMN = 0
SCINSIGHTS_TOPTALKERS_UPLINK_NAME_COLUMN = 1
SCINSIGHTS_TOPTALKERS_UPLINK_BPS_COLUMN = 6
SCINSIGHTS_TOPTALKERS_DATA_DEFS = \
	{
		"data_defs": [
    			{
			"reference_id": "topUplinkDD",
			"time": {
				},
			"filters": [
				],
			"reference_id": "topUplinkDD",
			"group_by": [
  				"sdwan.uplink.id"
				],
			"top_by": [
				{
				"direction": "desc",
				"id": "sum_traffic.total_bytes_ps"
				}
			],
			"columns": [
				"sdwan.uplink.id",
				"sdwan.uplink.name",
				"sdwan.site.id",
				"sdwan.site.name",
				"sdwan.wan.id",
				"sdwan.wan.name",
				"sum_traffic.total_bytes_ps"
				],
			"source": {
  				"name": "sdwan"
				},
			"limit": 10
			}
  		]
	}

SCINSIGHTS_TIMESERIES_UPLINK_DATADEF_INDEX = 0
SCINSIGHTS_TIMESERIES_START_TIME_COLUMN = 0
SCINSIGHTS_TIMESERIES_UPLINK_NAME_COLUMN = 2
SCINSIGHTS_TIMESERIES_SITE_NAME_COLUMN = 4
SCINSIGHTS_TIMESERIES_THROUGHPUT_COLUMN = 7
SCINSIGHTS_TIMESERIES_INTHROUGHPUT_COLUMN = 8
SCINSIGHTS_TIMESERIES_OUTTHROUGHPUT_COLUMN = 9
SCINSIGHTS_TIMESERIES_MAXTHROUGHPUT_COLUMN = 10
SCINSIGHTS_TIMESERIES_MAXINTHROUGHPUT_COLUMN = 11
SCINSIGHTS_TIMESERIES_MAXOUTTHROUGHPUT_COLUMN = 12
SCINSIGHTS_TIMESERIES_NUMMETRICS = 3
SCINSIGHTS_TIMESERIES_DATA_DEFS = \
	{
		"data_defs": [
    			{
			"reference_id": "topUplinkDD",
			"time": {
				},
			"filters": [
				],
			"reference_id": "topUplinkDD",
			"group_by": [
				"start_time",
  				"sdwan.uplink.id"
				],
			"top_by": [
				{
				"direction": "desc",
				"id": "sum_traffic.total_bytes_ps"
				}
			],
			"columns": [
				"start_time",
				"sdwan.uplink.id",
				"sdwan.uplink.name",
				"sdwan.site.id",
				"sdwan.site.name",
				"sdwan.wan.id",
				"sdwan.wan.name",
				"sum_traffic.total_bytes_ps",
				"sum_traffic.total_p2m_bytes_ps",
				"sum_traffic.total_m2p_bytes_ps",
#				"max_traffic.total_bytes_ps",
#				"max_traffic.total_p2m_bytes_ps",
#				"max_traffic.total_m2p_bytes_ps"
				],
			"source": {
  				"name": "sdwan"
				},
			}
  		]
	}


##### HELPER FUNCTIONS
# Run REST APIs to appliance and return result
# Assume 'payload' is JSON formatted
def scinsights_rest_api (action, path, appliance, access_token, payload = None):

	url = "https://" + appliance + path 

	bearer = "Bearer " + access_token
	headers = {"Authorization":bearer}

	if (action == "GET"):
		r = requests.get (url, headers=headers, verify=False)
	elif (action == "POST"):
		r = requests.post (url, headers=headers, data=json.dumps (payload), verify=False)
	elif (action == "PUT"):
		r = requests.put (url, headers=headers, data=json.dumps (payload), verify=False)
	elif (action == "DELETE"):
		r = requests.delete (url, headers=headers, verify=False)

	if (r.status_code not in [200, 201, 204]):
		print ("Status code was %s" % r.status_code)
		print ("Error: %s" % r.content)
		result = None
	else:
		if (("Content-Type" in r.headers.keys ()) and ("application/json" in r.headers ["Content-Type"])):
			result = json.loads (r.content) 
		elif (("Content-Type" in r.headers.keys ()) and ("application/x-gzip" in r.headers ["Content-Type"])):
			result = r.content
		else:
			result = r.text

	return result 


##### GENERAL FUNCTIONS

# ACCESS_TOKEN APPROACH

def scinsights_token_request (appliance, username, password):

	url = "https://" + appliance + "/api/mgmt.aaa/1.0/token"
	credentials = {"username":username, "password":password}
	payload = {"user_credentials":credentials, "generate_refresh_token":False}
	headers = {"Content-Type":"application/json"}

	r = requests.post (url, data=json.dumps(payload), headers=headers, verify=False)
	
	if (r.status_code not in [200, 201, 204]):
		print ("Status code was %s" % r.status_code)
		print ("Error %s" % r.content)
		return None
	else:
		result = json.loads (r.content)

	return result ["access_token"]

def scinsights_token_revoke (appliance):
	
	return

# SESSION KEY, SESSION ID APPROACH

# REST API Python wrapper to authenticate to the server (Login)
def scinsights_login (appliance, username, password):

	url = "https://" + appliance + "/api/common/1.0/login"
	credentials = {"username":username, "password":password}
	headers = {"Content-Type":"application/json"}

	r = requests.post(url, data=json.dumps(credentials), headers=headers, verify=False)

	if (r.status_code not in [200, 201, 204]):
		print ("Status code was %s" % r.status_code)
		print ("Error %s" % r.content)
		return None, None
	else:
		result = json.loads(r.content)

	return result["session_key"], result["session_id"]

def scinsights_logout (appliance, session_key, session_id):
	
	url = "https://" + appliance + "/api/common/1.0/logout"
	headers = {session_key:session_id, "Content-Type":"application/json"}

	r = requests.post (url, headers=headers, verify=False)

	if (r.status_code not in [200, 201, 204]):
		print ("Status code was %s" % r.status_code)
		print ("Error %s" % r.content)
		return
	
	return

##### MAIN FUNCTION

def scinsights_report_run (hostname, access_token, report_parameters):

	report_results = []

	# Run reports for this site
	report_run = scinsights_rest_api ("POST", "/api/npm.reports/1.0/instances", hostname, access_token, 
				payload = report_parameters)

	# Pull reports
	report_id = report_run ["id"]
	report_items = report_run ["data_defs"]
	for report_item in report_items:
		item_id = report_item ["id"]
		report_path = "/api/npm.reports/1.0/instances/items/%s/data_defs/items/%s" % (report_id, item_id)
		report_status = report_path + "/status"

		completed = False
		while (completed != True):
			report_update = scinsights_rest_api ("GET", report_status, hostname, access_token)

			state = report_update ["state"]
			if ((state == "pending") or (state == "initializing") or (state == "executing")):
				print ("State %s. Waiting for %s seconds ..." % (state, SCINSIGHTS_REPORT_WAIT))
				time.sleep (SCINSIGHTS_REPORT_WAIT)
			elif (state == "error"):
				completed = True
				error_messages = report_update ["messages"]

				for error_message in error_messages:
					print (error_message)
				return
			else:
				completed = True 


		report_data = report_path + "/data"
		report_result = scinsights_rest_api ("GET", report_data, hostname, access_token)

		delete_confirmation = scinsights_rest_api ("DELETE", report_path, hostname, access_token)

		report_results.append (report_result)

	return report_results

def scinsights_report_export (output_file, report_results):
	
	workbook = xlsxwriter.Workbook (output_file)
	header_format = workbook.add_format ({'bold':True,'text_wrap':True,'align':'center'})
	merge_format = workbook.add_format ({'align':'center','valign':'top','bold':True})
	time_format = workbook.add_format ({'num_format':'dd/mm/yy hh:mm'})
	tput_format = workbook.add_format ({'num_format':'#,##0.000'})

	# Output
	for report_result in report_results:
		if (report_result == None):
			continue

		for data_set in report_result:
			# Pull the site name from the report data
			site_name = data_set ["data"][SCINSIGHTS_TIMESERIES_UPLINK_DATADEF_INDEX] \
				[SCINSIGHTS_TIMESERIES_SITE_NAME_COLUMN]

			# Prepare structure for recording column headers
			uplinks_columns = []
			# Prepare structure for sorting rows by start time
			rows = {}

			data_values = data_set ["data"]
			for data_value in data_values:

				# Check if uplink exists in current list for column headers
				uplink = data_value [SCINSIGHTS_TIMESERIES_UPLINK_NAME_COLUMN]
				if uplink not in uplinks_columns:
					uplinks_columns.append (uplink)

				# Create dictionary with start time as key and list of uplink, throughput pair as values
				key = data_value [SCINSIGHTS_TIMESERIES_START_TIME_COLUMN]
				throughput = [data_value [SCINSIGHTS_TIMESERIES_THROUGHPUT_COLUMN], 
					data_value [SCINSIGHTS_TIMESERIES_INTHROUGHPUT_COLUMN],
					data_value [SCINSIGHTS_TIMESERIES_OUTTHROUGHPUT_COLUMN]]
			
				# If key doesn't exist
				if key not in rows.keys ():
					rows [key] = {}
				rows [key][uplink] = throughput
			
			# Worksheet per site
			worksheet = workbook.add_worksheet (site_name)
			worksheet.set_column ('A:M', SCINSIGHTS_OUTPUT_COLUMN_SPACING)
		
			# Column per start time & uplinks
			#     | UL 1 |     |     | UL 2 |     |     |
			# ST  | Avg  | In  | ... | Avg  | In  | ... | 
			# Currently, there are six metrics per uplink
			num_metrics = SCINSIGHTS_TIMESERIES_NUMMETRICS
			firstrow_startcol = 1 # Leave space for key - "Start Time"
			secondrow_headers = ["Start Time"]
			for uplinks_column in uplinks_columns:
				worksheet.merge_range (0, firstrow_startcol, 0, firstrow_startcol + num_metrics - 1, 
					uplinks_column, merge_format)
				secondrow_headers.extend (["Total Throughput", "Inbound Throughput", "Outbound Throughput"])
				firstrow_startcol += num_metrics
			worksheet.write_row (1, 0, secondrow_headers, header_format)
			worksheet.set_row (1, SCINSIGHTS_OUTPUT_HEADER_HEIGHT) # Set height for second row

			# Create uplink lookup table for matching throughput to proper uplink
			uplink_lookup = {k:v for v,k in enumerate (uplinks_columns)}

			# Row per start time & throughput
			data_row = 2 # Start after the two header rows
			for start_time in sorted (rows):
				# Excel displays time as days from 1/1/1900 and Unix time is seconds from 1/1/1970
				excel_time = float (start_time) / 86400 + 25569
				# In each row, align the values with the correct columns
				worksheet.write (data_row, 0, excel_time, time_format)
				for uplink_name, uplink_tputs in rows [start_time].items ():
					mbps_tputs = []
					for uplink_tput in uplink_tputs:
						# Convert from bytes per second 
						mbps_tputs.append(float (uplink_tput) * 8 / (1000 * 1000)) 
					worksheet.write_row (data_row, (uplink_lookup [uplink_name] * num_metrics) + 1, 
						mbps_tputs, tput_format)
				data_row += 1 # Move to next row

	while True:
		try:
			workbook.close ()
		except xlsxwriter.exceptions.FileCreateError as e:
			decision = raw_input ("Exception caught in writing workbook: %s.\n"
					"Try to write file again?" % e)
			if decision != 'n':
				continue
		break

	return True
		

def main():
	# set up arguments in appropriate variables
	parser = argparse.ArgumentParser (description="Python utilities to automate information collection or \
		 configuration tasks within SteelConnect CX Insights environments")
	parser.add_argument('--hostname', help="Hostname or IP address of the SteelConnect Insights appliance")
	parser.add_argument('--username', help="Username for the appliance")
	parser.add_argument('--password', help="Password for the username")
	parser.add_argument('--action', help="Action to perform: %s" % SCINSIGHTS_UTILITIES_ACTIONS)
	parser.add_argument('--actionfile', help="Settings file associated with action")
	parser.add_argument('--duration', help="Report timeframe, i.e. 'last 30 days'")
	parser.add_argument('--granularity', help="Report granularity, either minute ('60'), hour ('3600'), or day ('86400')")
	args = parser.parse_args()

	# Check inputs for required data and prep variables
	if (args.hostname == None or args.hostname == ""):
		print ("Please specify a hostname using --hostname")
		return
	if (args.username == None or args.username == ""):
		print ("Please specify a username using --username")
		return
	if (args.action == None or args.action == ""):
		print ("Please specify an action using --action")
		return

	# Check that action exist in set of known actions
	if not (args.action in SCINSIGHTS_UTILITIES_ACTIONS):
		print ("Action %s is unknown" % args.action)

	access_token = scinsights_token_request (args.hostname, args.username, args.password)
	if (access_token == None):
		print ("Failed to login to %s" % args.hostname)
		return

	### Also support timerange?
	if (args.duration == None or args.duration == ""):
		print ("Please specify a reporting timeframe using --duration")
		return
	if (args.granularity == None or args.granularity == ""):
		print ("Please specify a reporting timeframe using --granularity")
	duration = {"duration":args.duration,"granularity":args.granularity}

	# ACTION - site_summary
	if (args.action == "site_summary"):
		# Get list of site IDs
		result = scinsights_rest_api ("GET", "/api/npm.search/1.0/search?types=sdwan.site.name&limit=10000",
			args.hostname, access_token)
		
		# Set up input list for site reports and structure to capture results
		site_list = result ["items"]
		timeseries_results = []
		
		for site in site_list:

			if (site ["has_data"] == False):
				continue

			# Configure report parameters to get list of top uplinks over the duration for the site
			site_id = site ["sdwan.site.name"]["id"]			
			filter_str = "sdwan.site.id == %s" % site_id
			filter = {"value":filter_str}

			report_parameters = SCINSIGHTS_TOPTALKERS_DATA_DEFS
			report_parameters ["data_defs"][SCINSIGHTS_TOPTALKERS_UPLINK_DATADEF_INDEX]["time"] = duration
			report_parameters ["data_defs"][SCINSIGHTS_TOPTALKERS_UPLINK_DATADEF_INDEX]["filters"] = [filter]

			report_results = scinsights_report_run (args.hostname, access_token, report_parameters)

			# Run a time series report for each active uplink
			for report_result in report_results:

				if report_result ["meta"]["count"] == 0:
					print ("No data returned for hostname %s" % site ["sdwan.site.name"]["name"])
					continue

				# Filter uplinks to just the ones for which we want to get time series
				uplinks = []
				uplink_report = report_result ["data"]
				for uplink in uplink_report:
					# Define if uplink is "active"
					if (float (uplink [SCINSIGHTS_TOPTALKERS_UPLINK_BPS_COLUMN]) > 0.5) \
						and (uplink [SCINSIGHTS_TOPTALKERS_UPLINK_NAME_COLUMN] != "#N/D"):
						uplinks.append (uplink [SCINSIGHTS_TOPTALKERS_UPLINK_ID_COLUMN]) 

				# Configure report parameters
				if len (uplinks) == 0:
					continue
				uplink_str = ','.join (map (str, uplinks))
				filter_str = "%s and sdwan.uplink.id in (%s)" % (filter_str, uplink_str)
				filter = {"value":filter_str}

				report_parameters = SCINSIGHTS_TIMESERIES_DATA_DEFS
				report_parameters ["data_defs"][SCINSIGHTS_TIMESERIES_UPLINK_DATADEF_INDEX]["time"] = duration
				report_parameters ["data_defs"][SCINSIGHTS_TIMESERIES_UPLINK_DATADEF_INDEX]["filters"] = [filter]

				# Run reports	
				timeseries_result = scinsights_report_run (args.hostname, access_token, report_parameters)
				# Save result for uplink
				timeseries_results.append (timeseries_result)

		report_output_status = scinsights_report_export (SCINSIGHTS_OUTPUT_FILE, timeseries_results)
		if (report_output_status == False):
			print ("Error exporting to %s" % (SCINSIGHTS_OUTPUT_FILE))

	scinsights_token_revoke (args.hostname)

	return
		
if __name__ == "__main__":
	main()

