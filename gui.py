import PySimpleGUI as sg
from sys import platform
from openpyxl import load_workbook
import os
import moralstrength
from lexicon_use import form_text_vector
import estimators as estimators
import numpy as np
import threading

model_to_use = ''
isProcessingFiles = False
currentFile = ""
errorfiles = []

trans_list = dict()
lr_lst = dict() 

#iterate over radio buttons and find which model to use
def getModel(values):
	global model_to_use
#	pdb.set_trace()
	for model in estimators.models:
		if values[model]:
			model_to_use = model

def processTextWithMoral(text,moral):
	transformers = trans_list[moral]
	lr = lr_lst[moral]
	X = []
	for transformer in transformers.keys():
		if transformer == 'unigram':
			X_tmp = transformers[transformer].transform([' '.join(t) for t in text])
			X_tmp = X_tmp.toarray()
			X.append(X_tmp)
		elif transformer == 'simon':
			X_tmp = transformers[transformer].transform(text)
			X.append(X_tmp)
		else: 
			X_tmp = [form_text_vector(t, model=transformer) for t in text]    
			X.append(X_tmp)
	X = np.hstack(X)
	return lr.predict_proba(X)[:, 1][0]


def processExcelFile(inputfilename,outputfilename):
	wb = load_workbook(filename = inputfilename)
	sheet = wb[wb.sheetnames[0]]
	last_col = sheet.max_column + 1
	#first row is the header
	colidx = last_col
	for moral in moralstrength.moral_options_predictions:
		colidx = colidx + 1
		sheet.cell(row=1, column=colidx).value = moral
		
	#process remaining file
	for rowidx in range(2,sheet.max_row+1): 
		text = sheet.cell(row=rowidx, column=1).value
		text_processed = estimators.pp_pipe.transform([text])
		colidx = last_col
		for moral in moralstrength.moral_options_predictions:
			colidx = colidx + 1
			sheet.cell(row=rowidx, column=colidx).value = processTextWithMoral(text_processed,moral)
	wb.save(outputfilename)
	return
	
def processTextFile(inputfilename,outputfilename):
	with open(inputfilename, 'r') as f:
		with open(outputfilename, "w") as outf:
			outf.write("Input text\t"+"\t".join(moralstrength.moral_options_predictions)+"\n")
			for line in f:
				line = line.strip()
				text_processed = estimators.pp_pipe.transform([line])
				outf.write(line)
				for moral in moralstrength.moral_options_predictions:
					outf.write("\t"+str(processTextWithMoral(text_processed,moral)))
				outf.write("\n")
	return

def processFiles(filelist):
	#print('processfiles')
	files = filelist.split(";")
	#preload all stuff once and then work line-by-line
	#so large files can also be processed without loading them in-memory
	global lr_lst
	global trans_list
	for moral in moralstrength.moral_options_predictions:
		estim, transformers = estimators.select_processes(model_to_use, moral)
		lr, transformers = estimators.load_models(estim, transformers, moral)
		lr_lst[moral] = lr
		trans_list[moral] = transformers
			
	global isProcessingFiles, currentFile, errorfiles
	errorstring = ""
	errorfiles = []
	
	isProcessingFiles = True
	#print('isProcessing = True')
	for file in files:
		currentFile = "Currently processing "+file
		#print(file)
		try:
			isExcel = False
			basefilename, extension = os.path.splitext(file)
			if extension.startswith('.xls'):
				isExcel = True
			outputfile = basefilename + "_MoralStrength"+extension
			if not isExcel:
				processTextFile(file,outputfile)
			else:
				processExcelFile(file,outputfile)
		except Exception as e:
			print(e)
			errorfiles.append(file)
			errorstring = " (with errors)"
			continue
	isProcessingFiles = False
	currentFile = "All files processed"+errorstring

def analyzeText(text):
	results = moralstrength.string_moral_values(text)
	maxmoral = ""
	maxvalue = -1
	for moral in results:
		if results[moral] > maxvalue:
			maxvalue = results[moral]
			maxmoral = moral
		window.Element(moral+"_result").Update("%.3f" % results[moral])
	window.Element(maxmoral+"_result").Update("%.3f (HIGHEST)" % maxvalue)

if platform == "darwin":
	openFileButton = sg.FileBrowse('Select one file', target="files")
	openManyFilesButton = sg.FilesBrowse('Select multiple files', target="files")
else:
	openFileButton = sg.FileBrowse('Select one file', target="files", file_types=(("Text Files", "*.txt"), ("Excel Files", "*.xlsx"), ("ALL Files", "*.*")))
	openManyFilesButton = sg.FilesBrowse('Select multiple files', target="files", file_types=(("Text Files", "*.txt"), ("Excel Files", "*.xlsx"), ("ALL Files", "*.*")))
	


#The first tab is for direct text entry. It has a big text box, a button, and a 2*6 grid for results + labels
output_values = [[sg.Text('Care/Harm', size=(20, 1)), sg.Input('0',key='care_result')],
		[sg.Text('Fairness/Cheating', size=(20, 1)), sg.Input('0',key='fairness_result')],
		[sg.Text('Loyalty/Betrayal', size=(20, 1)),	 sg.Input('0',key='loyalty_result')],
		[sg.Text('Authority/Subversion', size=(20, 1)), sg.Input('0',key='authority_result')],
		[sg.Text('Purity/Degradation', size=(20, 1)), sg.Input('0',key='purity_result')],
		[sg.Text('Non-moral', size=(20, 1)), sg.Input('0',key='non-moral_result')]]
tab1_layout =  [[sg.Text('Enter text to annotate:')],	  
	[sg.Multiline('',size=(88, 20), key='inputtext')],		
	[sg.Button('Analyze text')],
	[sg.Text('The output is the estimated probability of the text being relevant to either a vice or virtue of the corresponding moral trait.\nSince the system is trained on tweets, try not to analyze a long text!')],
	[sg.Column(output_values)]]	   
	
#the second tab is for analyzing one or more files	
tab2_layout = [[sg.Text(
'''Select one or more files to analyze. If you select a text file, the file results are calculated *per line*.
The output file will contain the input text lines and the 6 predictions, separated by tabs.
	
You can also select an Excel file; the results are calculated on the text in the first column, row by row.
Rrow A is considered a header and *is ignored*.
The results are put in the first available column, and a new file is saved.

The output will always be saved in "[old_filename]_MoralStrength", and the file will be overwritten silently!

As in the other tab, the output is the estimated probability of the text being relevant to either
a vice or virtue of the corresponding moral trait.''')],		
	[openFileButton, openManyFilesButton] ,
	[sg.Text('Selected file(s):')],
	[sg.Text('', key='files', size=(88, 2))],
	[sg.Button('Analyze file(s)')],
	[sg.Text('', key='currentfile', size=(88, 1))],
	]

## the third tab is for configuring the options (i.e., which model to use)
tab3_layout =  [[sg.Text('Select which model should be used for predicting the moral texts:')],
#	[sg.Radio('simon', key='simon', group_id="ModelChoiceRadios")],
	[sg.Radio('unigram', key='unigram', group_id="ModelChoiceRadios")],
	[sg.Radio('count', key='count', group_id="ModelChoiceRadios")],
	[sg.Radio('freq', key='freq', group_id="ModelChoiceRadios")],
#Simon model requires an embeddings package
# 	[sg.Radio('simon+count', key='simon+count', group_id="ModelChoiceRadios")],
# 	[sg.Radio('simon+freq', key='simon+freq', group_id="ModelChoiceRadios")],
# 	[sg.Radio('simon+count+freq', key='simon+count+freq', group_id="ModelChoiceRadios")],
	[sg.Radio('unigram+count', key='unigram+count', group_id="ModelChoiceRadios")],
	[sg.Radio('unigram+freq', key='unigram+freq', group_id="ModelChoiceRadios", default=True)],
	[sg.Radio('unigram+count+freq', key='unigram+count+freq', group_id="ModelChoiceRadios")],
# 	[sg.Radio('simon+unigram+count', key='simon+unigram+count', group_id="ModelChoiceRadios")],
# 	[sg.Radio('simon+unigram+freq', key='simon+unigram+freq', group_id="ModelChoiceRadios")],
# 	[sg.Radio('simon+unigram+count+freq', key='simon+unigram+count+freq', group_id="ModelChoiceRadios")],
	[sg.Text('''You can read what each model does in our paper:
MoralStrength: Exploiting a Moral Lexicon and Embedding Similarity for Moral Foundations Prediction
Oscar Araque, Lorenzo Gatti, Kyriaki Kalimeri
(currently in review at Expert Systems with Applications, but available at https://arxiv.org/abs/1904.08314)''')]]	 

# fourth tab: the paper in a textbox that's easy to copy for reference
tab4_layout = [[sg.Text('If you use this tool, please cite the following paper:')],
				[sg.Multiline('''MoralStrength: Exploiting a Moral Lexicon and Embedding Similarity for Moral Foundations Prediction
Oscar Araque, Lorenzo Gatti, Kyriaki Kalimeri

Currently in review at Expert Systems with Applications, but available at 
https://arxiv.org/abs/1904.08314''',size=(88, 20))]
				]

layout = [[sg.TabGroup([
			[sg.Tab('Direct text entry', tab1_layout, tooltip='Here you can input some text directly and get a prediction, it is useful for interactive testing'), 
			 sg.Tab('Work on files', tab2_layout, tooltip='Here you can select one or more files to be processed, which is useful for batch works'),
			 sg.Tab('Model selection', tab3_layout, tooltip='Here you can decide which ML model to use for the prediction'),
			sg.Tab('Info', tab4_layout)			
			 ]])]
		]





# Create the Window
window = sg.Window('MoralStrength', layout)
# Event Loop to process "events"
threads = []
while True:				
    #update the windows every 200 msec
	event, values = window.Read(timeout=200)
	if (isProcessingFiles):
		window.Element('currentfile').Update(currentFile)

	if event in (None, 'Cancel'):
		break
	
	for thread in threads:
		if not thread.isAlive():
			thread.join()
			threads.remove(thread)
			window.Element('currentfile').Update(currentFile)
			if len(errorfiles)>0:
				sg.PopupError('The following files could not be processed correctly:'+'  '.join(errorfiles))

	
	if event == 'Analyze text':
		if "inputtext" in values and not values["inputtext"].isspace():
			thread = threading.Thread(target = analyzeText, args = (values["inputtext"],))
			thread.start()
			threads.append(thread)
			#analyzeText()
		else:
			window.Element('inputtext').Update("Write or paste some text first!")
	if event == "Analyze file(s)":
		window.Element('currentfile').Update("")
		getModel(values)	
		#ugh... why is the target= of the open file not working? I don't know
		if 'text' in window.Element('files').TKText.keys() and not window.Element('files').TKText['text'].isspace():
			filenames = window.Element('files').TKText['text']
			thread = threading.Thread(target = processFiles, args = (filenames,))
			thread.start()
			threads.append(thread)
		else:
			window.Element('files').Update("Select one (or more) files first!")
window.Close()
