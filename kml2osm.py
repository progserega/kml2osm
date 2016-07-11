#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#from lxml import etree
from lxml import etree
#from fastkml import kml
import sys
import getopt
import re
import os
#from shapely.geometry import Point, LineString, Polygon
#from shapely.geometry import MultiPoint, MultiLineString, MultiPolygon
#from shapely.geometry.polygon import LinearRing


#DEBUG=False
DEBUG=True

def write_osm_xml(out_file,nodes,lines):
	f=open(out_file,"w+")
	f.write("""<?xml version='1.0' encoding='UTF-8'?>
<osm version='0.6' upload='true' generator='JOSM'>
<bounds minlat='39.21' minlon='128.24' maxlat='53.02' maxlon='142.44' origin='OpenStreetMap server' />
""")

# Точки:
	for node_id in nodes:
		node=nodes[node_id]
		tags=node["tags"]
		f.write("	<node id='%(id)d' action='modify' visible='true' lat='%(lat)f' lon='%(lon)f' >\n" % {\
				"id":node_id,\
				"lat":node["lat"],\
				"lon":node["lon"],\
				})
		for k in tags:
			f.write("		<tag k='%(key)s' v='%(value)s' />\n" % {"key":k, "value":tags[k]})
		f.write("	</node>\n")
# линии:
	for way_id in lines:
		way=lines[way_id]
		tags=way["tags"]
		f.write("	<way id='%(id)d' action='modify' visible='true'>\n" %{\
				"id":node_id\
				})
		for node_id in way["nodes"]:
			f.write("		<nd ref='%(id)d' />\n" % {"id":node_id})
		for k in tags:
			f.write("		<tag k='%(key)s' v='%(value)s' />\n" % {"key":k, "value":tags[k]})
		f.write("	</way>\n")
			
		



	f.write("""</osm>""")
	f.close
	

def print_help():
	os.write(2,"""
This is convertor kml->osm
	This programm read kml-file (Google Earth geo-data) and write osm-file (OpenStreetMap xml)
	Use:            
		kml2osm -i in.kml -o out.osm

options: 
	-i file - input file with kml 
	-o file - output file with osm
	-d - debug output
	-h - this help
need 2 parametr: input and output files.
Use -h for help.
exit!
""")

def parse_opts():
	inputfile = ''
	outputfile = ''
	try:
		opts, args = getopt.getopt(sys.argv[1:],"hdr:i:o:",["help","debug","rules=","infile=","outfile="])
	except getopt.GetoptError as err:
		os.write(2, str(err) ) # will print something like "option -a not recognized"
		print_help()
		sys.exit(2)

	for opt, arg in opts:
		if opt in ("-h", "--help"):
			print_help()
			sys.exit()
		elif opt in ("-i", "--infile"):
			global in_file
			in_file = arg
		elif opt in ("-o", "--outfile"):
			global out_file
			out_file = arg
		elif opt in ("-d", "--debug"):
			global DEBUG 
			DEBUG = True

def find_node_by_coord(nodes, lon,lat):
	for node_id in nodes:
		if nodes[node_id]["lat"]==lat and nodes[node_id]["lon"]==lon:
			return node_id
	return None

def process_folder(root,ns,nodes,lines,note):
	for folder in root.findall(ns+"Folder"):
		folder_name=""
		folder_name_tag=folder.find(ns+"name")
		if folder_name_tag!=None:
			folder_name=folder_name_tag.text
		# Обрабатываем точки в текущей директории:
		process_placemark_points(folder,ns,nodes,lines,folder_name,note)
		# Обрабатываем линии в текущей директории:
		process_placemark_lines(folder,ns,nodes,lines,folder_name,note)

		# Погружаемся на уровень ниже:
		process_folder(folder,ns,nodes,lines,note)

def process_placemark_points(root,ns,nodes,lines,line_name,note):
	for p in root.findall(ns+"Placemark"):
		tag=p.find(ns+"Point")
		if tag!=None:
			process_point(p,ns,nodes,line_name,note)

def process_placemark_lines(root,ns,nodes,lines,line_name,note):
	for p in root.findall(ns+"Placemark"):
		tag=p.find(ns+"LineString")
		if tag!=None:
			process_line(p,ns,nodes,lines,line_name,note)

def process_point(p,ns,nodes,line_name,note):
	global current_node_id
	node={}
	tags={}
	tags["ref"]=""
	tag=p.find(ns+"name")
	if tag!=None:
		tags["ref"]=tag.text
	point=p.find(ns+"Point")
	if point==None:
		print("ERROR find point in process_point()!")
		return False
	coord=point.find(ns+"coordinates")
	if coord==None:
		print("ERROR find coordinates in process_point()!")
		return False
	node["lon"]=float(coord.text.split(",")[0])
	node["lat"]=float(coord.text.split(",")[1])
	tags["ele"]=float(coord.text.split(",")[2])
	lookAt=p.find(ns+"LookAt")
	if lookAt!=None:
		range_tag=lookAt.find(ns+"range")
		if range_tag!=None:
			range_value=int(range_tag.text)
			if range_value > 1000:
				node["type"]="vl"
			else:
				node["type"]="kl"
	if DEBUG:
		print("DEBUG: line_name: ",line_name)
	try:
		tags["voltage"]=int(line_name.split("кВ")[0].split("ВЛ")[1])*1000
	except:
		print("DEBUG: can not find voltage in '%s'" % line_name)
		
	tags["source"]="survey"
	tags["source:note"]=note
	tags["note"]=line_name
	node["tags"]=tags
	node["id"]=current_node_id
	nodes[current_node_id]=node
	current_node_id-=1
	return True
		
def process_line(p,ns,nodes,lines,line_name,note):
	name=""
	line={}
	tags={}
	tags["name"]=line_name
	if DEBUG:
		print("DEBUG: line_name: ",line_name)
	try:
		tags["voltage"]=int(line_name.split("кВ")[0].split("ВЛ")[1])*1000
	except:
		print("DEBUG: can not find voltage in '%s'" % line_name)
	
	tags["source"]="survey"
	tags["source:note"]=note
	line["name"]=tags["name"]
	line["tags"]=tags
	line["nodes"]=[]

	tag=p.find(ns+"name")
	if tag!=None:
		name=tag.text
	LineString=p.find(ns+"LineString")
	if LineString==None:
		print("ERROR find LineString in process_line()!")
		return False
	coordinates=LineString.find(ns+"coordinates")
	if coordinates==None:
		print("ERROR find coordinates in process_line()!")
		return False
	coord_text=coordinates.text.replace('\t','').replace('\n','')
	if DEBUG:
		print("DEBUG: coordinates: %s" % coord_text)
	coords=coord_text.split(" ")
	# Формируем список точек из координат точек линии:
	points=[]
	for coord in coords:
		point={}
		if coord=='':
			print("ERROR coord=''")
			continue
		if DEBUG:
			print("DEBUG: coord: '%s'" % coord)
		point["lon"]=float(coord.split(",")[0])
		point["lat"]=float(coord.split(",")[1])
		point["ele"]=float(coord.split(",")[2])
		points.append(point)
		if DEBUG:
			print("DEBUG: append point:", point)
	# Запускаем функцию добавления LineString в существующие линии или в новую:
	append_line_to_lines(line,points,nodes,lines)

def append_line_to_lines(line,points,nodes,lines):
	global current_way_id
	num_points_in_kml_line=len(points)
	# Берём первую точку в линии:
	first_point_kml_line_id=find_node_by_coord(nodes,points[0]["lon"], points[0]["lat"] )
	if first_point_kml_line_id == None:
		print("ERROR find Point in nodes! (%f,%f)" % (\
					nodes,points[0]["lon"], points[0]["lat"] ))
		return False
	first_point_kml_line = nodes[first_point_kml_line_id]
	# Берём последнюю точку в линии:
	last_point_kml_line_id=find_node_by_coord(nodes, \
			points[num_points_in_kml_line-1]["lon"],\
			points[num_points_in_kml_line-1]["lat"])
	if last_point_kml_line_id == None:
		print("ERROR find Point in nodes! (%f,%f)" % (\
			points[num_points_in_kml_line-1]["lon"],\
			points[num_points_in_kml_line-1]["lat"]))
		return False
	last_point_kml_line=nodes[last_point_kml_line_id]
# Перебираем существующие линии с таким именем:
	add_flag=False
	for line_id in lines:
		l=lines[line_id]
		if DEBUG:
			print("l['name']=",l["name"])
			print("line['tags']['name']=",line["tags"]["name"])
		if l["name"]==line["tags"]["name"]:
			# Берём первую и последнюю точку в линии:
			num_points_in_line=len(l["nodes"])
			if DEBUG:
				print("num_points_in_line=",num_points_in_line)
			l_fist_node_id=0
			l_last_node_id=0
			if num_points_in_line == 1:
				l_fist_node_id=l["nodes"][0]
				l_last_node_id=l["nodes"][0]
			elif num_points_in_line >=2:
				l_fist_node_id=l["nodes"][0]
				l_last_node_id=l["nodes"][num_points_in_line-1]
			else:
				# Пропускаем пустую линию
				continue
			#Проверяем, можно ли добавить наш кусочик из kml в начало или конец этой линии:
			if DEBUG:
				print("l_fist_node_id=",l_fist_node_id)
				print("l_last_node_id=",l_last_node_id)
				print("first_point_kml_line=",first_point_kml_line)
				print("last_point_kml_line=",last_point_kml_line)
			l_fist_node=nodes[l_fist_node_id]
			l_last_node=nodes[l_last_node_id]

			# Первая точка линии kml совпадает с последней точкой в линии:
			if l_last_node["lat"]==first_point_kml_line["lat"] and l_last_node["lon"] == first_point_kml_line["lon"] and l["type"] == first_point_kml_line["type"]:
				# Просто добавляем в конец все точки из kml:
				for i in range(1,num_points_in_kml_line-1):
					id_node=find_node_by_coord(nodes, points[i]["lon"], points[i]["lat"] )
					if id_node == None:
						print("ERROR find Point in nodes! (%f,%f)" % (points[i]["lon"], points[i]["lat"] ))
					else:
						if id_node not in l["nodes"]:
							l["nodes"].append(id_node)
				add_flag=True
			# Последняя точка линии kml совпадает с последней точкой в линии:
			if l_last_node["lat"]==last_point_kml_line["lat"] and l_last_node["lon"] == last_point_kml_line["lon"] and l["type"] == last_point_kml_line["type"]:
				# добавляем в конец все точки из kml (наоборот, от предпоследней к первой):
				for i in range(num_points_in_kml_line-2,0):
					id_node=find_node_by_coord(nodes, points[i]["lon"], points[i]["lat"] )
					if id_node == None:
						print("ERROR find Point in nodes! (%f,%f)" % (points[i]["lon"], points[i]["lat"] ))
					else:
						if id_node not in l["nodes"]:
							l["nodes"].append(id_node)
				add_flag=True

			# Первая точка линии kml совпадает с первой точкой в линии:
			if l_fist_node["lat"]==first_point_kml_line["lat"] and l_fist_node["lon"] == first_point_kml_line["lon"] and l["type"] == first_point_kml_line["type"]:
				# Вставляем:
				for i in range(1,num_points_in_kml_line-1):
					id_node=find_node_by_coord(nodes, points[i]["lon"], points[i]["lat"] )
					if id_node == None:
						print("ERROR find Point in nodes! (%f,%f)" % (points[i]["lon"], points[i]["lat"] ))
					else:
						if id_node not in l["nodes"]:
							l["nodes"].insert(0,id_node)
				add_flag=True
			# Последняя точка линии kml совпадает с первой точкой в линии:
			if l_fist_node["lat"]==last_point_kml_line["lat"] and l_fist_node["lon"] == last_point_kml_line["lon"] and l["type"] == last_point_kml_line["type"]:
				# Вставляем "наоборот":
				for i in range(num_points_in_kml_line-2,0):
					id_node=find_node_by_coord(nodes, points[i]["lon"], points[i]["lat"] )
					if id_node == None:
						print("ERROR find Point in nodes! (%f,%f)" % (points[i]["lon"], points[i]["lat"] ))
					else:
						if id_node not in l["nodes"]:
							l["nodes"].insert(0,id_node)
				add_flag=True
	if add_flag==False:
		# Тогда добавляем в нашу новую линию:
		for p in points:
			id_node=find_node_by_coord(nodes, p["lon"], p["lat"])
			if id_node == None:
				print("ERROR find point in nodes! (%f,%f)" % (p["lon"], p["lat"]))
			else:
				if id_node not in line["nodes"]:
# Если тип не установлен (новая линия без точек:)
					if "type" not in line:
						# ставим тип из первой точки:
						line["type"]=nodes[id_node]["type"]
					else:
						# линия уже имеет тип, а значит и точки:
						if line["type"]!=nodes[id_node]["type"]:
							#линия имеет другой тип, чем новая точка. Нужно "закрыть" текущую линию и добавить новую и в новую уже добавить эту точку:
							# перед этим копируем нужные теги:
							tags={}
							tags["name"]=line["tags"]["name"]
							if "voltage" in line["tags"]:
								tags["voltage"]=line["tags"]["voltage"]
							tags["source"]="survey"
							tags["source:note"]=line["tags"]["source:note"]
							# Закрываем:
							line["id"]=current_way_id
							if len(line["nodes"])>0:
								lines[current_way_id]=line
# Создаём новую линию:
							line={}
							line["name"]=tags["name"]
							line["tags"]=tags
							line["nodes"]=[]
							line["type"]=nodes[id_node]["type"]
							current_way_id-=1
					line["nodes"].append(id_node)

	if len(line["nodes"])>0:
		line["id"]=current_way_id
		lines[current_way_id]=line
		current_way_id-=1
	return True

		

#################  Main  ##################

in_file=""
out_file=""
DEBUG=True

parse_opts()
if in_file=='' or out_file=='':
	print_help()
	sys.exit(2)

kml = etree.parse(in_file)
kml_root = kml.getroot()

lines={}
nodes={}

current_node_id=-1
current_way_id=-1

# name space:
ns="{http://www.opengis.net/kml/2.2}"

doc=kml_root.find(ns+"Document")
docname=doc.find(ns+"name").text

process_folder(doc,ns,nodes,lines,docname)
write_osm_xml(out_file,nodes,lines)
