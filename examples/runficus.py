import ficus
import os


input_file = 'example.xlsx'

result_folder = 'result'
result_name = os.path.splitext(os.path.split(input_file)[1])[0]
result_dir = ficus.prepare_result_directory(result_folder,result_name)

prob = ficus.run_ficus(input_file, opt = 'glpk')

ficus.report(prob, result_dir)
ficus.result_figures(result_dir,prob=prob, show=True)

