#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#from lxml import etree
from fastkml import kml
import sys
import getopt
import re
import os
from shapely.geometry import Point, LineString, Polygon
from shapely.geometry import MultiPoint, MultiLineString, MultiPolygon
from shapely.geometry.polygon import LinearRing


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
		f.write("	<way id='%(id)d' action='modify' visible='true'>" %{\
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
		

#################  Main  ##################

in_file=""
out_file=""
DEBUG=True

parse_opts()
if in_file=='' or out_file=='':
	print_help()
	sys.exit(2)

# KML read:
doc = open(in_file).read()
k = kml.KML()
k.from_string(doc)
features = list(k.features())

lines={}
nodes={}

current_node_id=-1
current_way_id=-1


for f1 in k.features():
	if DEBUG:
		print("f1: name=%s, description=%s" %(f1.name, f1.description))
	for f2 in f1.features():
		if DEBUG:
			print (f2)
			print("f2: name=%s, description=%s" %(f2.name, f2.description))
		for f3 in f2.features():
			if DEBUG:
				print (f3)
				print("f3: name=%s, description=%s" %(f3.name, f3.description))
# берём напряжение:
			voltage=int(f3.name.split("кВ")[0].split("ВЛ")[1])
			if DEBUG:
				print("DEBUG: voltage=%d" % voltage)
			for f4 in f3.features():
				if DEBUG:
					print (f4)
					print("f4: name=%s, description=%s" %(f4.name, f4.description))
# Линия
				line={}
				tags={}
				tags["name"]=f4.name
				tags["voltage"]=voltage*1000
				tags["source"]="survey"
				tags["source:note"]=f1.name
				line["name"]=tags["name"]
				line["tags"]=tags
				line["nodes"]=[]
#Опоры (сначала все опоры, т.к. они должны быть все для данной линии, чтобы потом соединять из них пролёты):
				for f5 in f4.features():
					if DEBUG:
						print (f5)
#if "Point" in f5.features():
						print("f5: lat=%s" %(f5))
						print("f5: name=%s, description=%s" %(f5.name, f5.description))
#print("f5: lat=%s" %(f5.Point.coordinates))
						print("f5: geom type:" ,f5.geometry.geom_type)
						print("f5: geom:" ,f5.geometry)
					if f5.geometry.geom_type == "Point":
						if DEBUG:
							print("x=%f, y=%f" %(float(f5.geometry.x), float(f5.geometry.y)))
						node={}
						tags={}
						node["lon"]=float(f5.geometry.x)
						node["lat"]=float(f5.geometry.y)
						tags["id"]=current_node_id

#					print("f5: ",f5.etree_element())
						if "Point" in f5.etree_element().keys():
							print("found Point: ", f5.etree_element.get("Point"))
						for tag in f5.etree_element():
							print("tag: '%s'" % tag.tag)
								
#						sys.exit(0)


#					if int(f5.LookAt.range) == 1000:
#							# кабельная линия
#							#tags["power"]="link"
#							node["type"]="kl"
#						elif int(f5.range) == 1030:
#							# воздушная линия
#							tags["power"]="tower"
#							node["type"]="vl"
	
						tags["ref"]=f5.name
						tags["voltage"]=voltage*1000
						tags["source"]="survey"
						tags["source:note"]=f1.name
						tags["note"]=f4.name
						node["tags"]=tags

# добавляем в общий список точек:
						nodes[current_node_id]=node
						current_node_id-=1
				
				# Теперь обрабатываем линии:
				for f5 in f4.features():
					if DEBUG:
						print (f5)
#if "Point" in f5.features():
						print("f5: lat=%s" %(f5))
						print("f5: name=%s, description=%s" %(f5.name, f5.description))
#print("f5: lat=%s" %(f5.Point.coordinates))
						print("f5: geom type:" ,f5.geometry.geom_type)
						print("f5: geom:" ,f5.geometry)
						

					if f5.geometry.geom_type == "LineString":
						num_points_in_kml_line=len(list(f5.geometry.coords))
# Берём первую точку в линии:
						first_point_kml_line=find_node_by_coord(nodes,Point(list(f5.geometry.coords)[0]).x, Point(list(f5.geometry.coords)[0]).y  )
						if first_point_kml_line == None:
							print("ERROR find Point in nodes! (%f,%f)" % (Point(list(f5.geometry.coords)[0]).x, Point(list(f5.geometry.coords)[0]).y) )
							continue
# Берём последнюю точку в линии:
						last_point_kml_line=find_node_by_coord(nodes, Point(list(f5.geometry.coords)[num_points_in_kml_line-1]).x, Point(list(f5.geometry.coords)[num_points_in_kml_line-1]).y  )
						if last_point_kml_line == None:
							print("ERROR find Point in nodes! (%f,%f)" % (Point(list(f5.geometry.coords)[num_points_in_kml_line-1]).x, Point(list(f5.geometry.coords)[num_points_in_kml_line-1]).y) )
							continue
# Перебираем существующие линии с таким именем:
						add_flag=False
						for l in lines:
							if l["name"]==line["tags"]["name"]:
								# Берём первую и последнюю точку в линии:
								num_points_in_line=len(l["nodes"])
								l_fist_node_id=0
								l_last_node_id=0
								if num_points_in_line == 1:
									l_fist_node_id=l["nodes"][0]
									l_fist_node_id=l["nodes"][0]
								elif num_points_in_line >=2:
									l_fist_node_id=l["nodes"][0]
									l_last_node_id=dl["nodes"][num_points_in_line-1]
								else:
									# Пропускаем пустую линию
									continue
								#Проверяем, можно ли добавить наш кусочик из kml в начало или конец этой линии:

								# Первая точка линии kml совпадает с последней точкой в линии:
								if nodes[l_last_node_id]["lat"]==first_point_kml_line["lat"] and nodes[l_last_node_id].lon == first_point_kml_line["lon"] and l["type"] == first_point_kml_line["type"]:
									# Просто добавляем в конец все точки из kml:
									for i in range(1,num_points_in_kml_line-1):
										id_node=find_node_by_coord(nodes, list(f5.geometry.coords)[i].x, list(f5.geometry.coords)[i].y )
										if id_node == None:
											print("ERROR find Point in nodes! (%f,%f)" % (list(f5.geometry.coords)[i].x, list(f5.geometry.coords)[i].y) )
										else:
											if id_node not in l["nodes"]:
												l["nodes"].append(id_node)
									add_flag=True
								# Последняя точка линии kml совпадает с последней точкой в линии:
								if nodes[l_last_node_id]["lat"]==last_point_kml_line["lat"] and nodes[l_last_node_id]["lon"] == last_point_kml_line["lon"] and l["type"] == last_point_kml_line["type"]:
									# добавляем в конец все точки из kml (наоборот, от предпоследней к первой):
									for i in range(num_points_in_kml_line-2,0):
										id_node=find_node_by_coord(nodes, list(f5.geometry.coords)[i].x, list(f5.geometry.coords)[i].y )
										if id_node == None:
											print("ERROR find Point in nodes! (%f,%f)" % (list(f5.geometry.coords)[i].x, list(f5.geometry.coords)[i].y) )
										else:
											if id_node not in l["nodes"]:
												l["nodes"].append(id_node)
									add_flag=True
	
								# Первая точка линии kml совпадает с первой точкой в линии:
								if nodes[l_fist_node_id]["lat"]==first_point_kml_line["lat"] and nodes[l_fist_node_id]["lon"] == first_point_kml_line["lon"] and l["type"] == first_point_kml_line["type"]:
									# Вставляем:
									for i in range(1,num_points_in_kml_line-1):
										id_node=find_node_by_coord(nodes, list(f5.geometry.coords)[i].x, list(f5.geometry.coords)[i].y )
										if id_node == None:
											print("ERROR find Point in nodes! (%f,%f)" % (list(f5.geometry.coords)[i].x, list(f5.geometry.coords)[i].y) )
										else:
											if id_node not in l["nodes"]:
												l["nodes"].insert(0,id_node)
									add_flag=True
								# Последняя точка линии kml совпадает с первой точкой в линии:
								if nodes[l_fist_node_id]["lat"]==last_point_kml_line["lat"] and nodes[l_fist_node_id]["lon"] == last_point_kml_line["lon"] and l["type"] == last_point_kml_line["type"]:
									# Вставляем "наоборот":
									for i in range(num_points_in_kml_line-2,0):
										id_node=find_node_by_coord(nodes, list(f5.geometry.coords)[i].x, list(f5.geometry.coords)[i].y )
										if id_node == None:
											print("ERROR find Point in nodes! (%f,%f)" % (list(f5.geometry.coords)[i].x, list(f5.geometry.coords)[i].y) )
										else:
											if id_node not in l["nodes"]:
												l["nodes"].insert(0,id_node)
									add_flag=True
						if add_flag==False:
							# Тогда добавляем в нашу новую линию:
							for p in list(f5.geometry.coords):
								id_node=find_node_by_coord(nodes, Point(p).x, Point(p).y)
								if id_node == None:
									print("ERROR find Point in nodes! (%f,%f)" % (Point(p).x, Point(p).y))
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
												line["id"]=current_way_id
												lines[current_way_id]=line
# Создаём новую линию:
												line={}
												tags={}
												tags["name"]=f4.name
												tags["voltage"]=voltage*1000
												tags["source"]="survey"
												tags["source:note"]=f1.name
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

write_osm_xml(out_file,nodes,lines)


#kml = etree.parse(in_file)
#kml_root = osm.getroot()
#print (etree.tostring(osm_root,pretty_print=True, encoding='unicode'))

#for node in osm_root:
#	if DEBUG:
#		print node.tag
#	if node.tag=="bounds":
#		continue
#	# Формируем списки точек, линий, отношений:
#	if node.tag=="node":
#		if DEBUG:
#			print ("DEBUG: node.keys: ", node.keys())
#		nodes[node.get("id")]=node
#	if node.tag=="way":
#		if DEBUG:
#			print ("DEBUG: node.keys: ", node.keys())
#		ways[node.get("id")]=node

#if DEBUG:
#	print (etree.tostring(osmpatch,pretty_print=True, encoding='unicode'))

#string=etree.tostring(kml, xml_declaration=True, encoding='UTF-8', pretty_print=True )
#f=open(out_file,"w+")
#f.write(string)
#f.close

#print ("nodes", nodes)
#for i in nodes:
#	for key in nodes[i].keys():
#		print (key,"=",nodes[i].get(key))


