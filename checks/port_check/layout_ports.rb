#!/usr/bin/ruby
# usage: layout_ports.rb <layoutFile> <cellName>
#
# Runs klayout (in batch) to get the ports of a cell in a layout file.
# Script starts as regular ruby, then exec's via klayout passing self to it.
# (klayout requirement is this script-name *must* end in .rb).
#
in_klayout=$in_klayout
if in_klayout.to_s.empty?
  this_script = $0
  layoutFile = ARGV[0]
  cellName = ARGV[1]
  portLayers = ARGV[2]

  if layoutFile == "--version" || layoutFile == "-v"
    # these options don't prevent klayout from initializing ~/.klayout unfortunately...
    exec "klayout -nc -rx -zz -v"
  end

  if ARGV.length != 3
    puts "ERROR, must give two arguments, usage: layout_ports.rb <layoutFile> <cellName> <portLayers>"
    puts "  It's an error if <cellName> unbound (referenced by others, not defined)."
    puts "  But that's the only unbound checked, no other cells checked or reported."
    puts "Exit-status: 0 on success; 1 on I/O or usage error; 2 unbound. See also gdsAllcells.rb"
    exit 1
  end


  # construct command from our script arguments, replace self with klayout...
  exec "klayout -nc -zz -rx \
	-rd in_klayout=1 \
	-rd file=#{layoutFile} \
	-rd topcell=#{cellName} \
	-rd ports=\"#{portLayers}\" \
	-r #{this_script}"
end

#
# to just read a layout in batch (no useful info printed):
#   klayout -d 40 -z xyz.gds >& klayout.read.log
#
#   -d : debug level, no details during GDS-reading however, try 20 or 40 or (timing too:) 21 or 41
#   -z/-zz : -z pseudo-batch mode, still needs X-DISPLAY connection; -zz true batch
#   -nc : don't use/update configuration file
#   -rx : disable built-in macros, stuff not needed for batch usually
#   -rd : define variables the script can reference
#

layoutFile = $file
cellName = $topcell
portLayers = $ports.split(" ")

if layoutFile == ""
  STDERR.puts "ERROR: missing layoutFile argument, usage: layout_ports.rb <layoutFile> <cellName> <portLayers>"
  exit 1
elsif cellName == ""
  STDERR.puts "ERROR: missing cellName argument, usage: layout_ports.rb <layoutFile> <cellName> <portLayers>"
  exit 1
elsif portLayers.empty?
  STDERR.puts "ERROR: missing port layer list argument, usage: layout_ports.rb <layoutFile> <cellName> <portLayers>"
  exit 1
end

include RBA

begin
  puts "Reading file #{layoutFile} for cell #{cellName}."
  puts "Looking for ports on #{portLayers}."
  layout = Layout.new
  layout.read(layoutFile)
  dbu = layout.dbu
  puts "dbu: #{dbu}"

  errs = 0

  # does not catch case where cell.bbox -> "()"
  if ! layout.has_cell?(cellName)
    STDERR.puts "ERROR: layout does not have the cell #{cellName}"
    STDOUT.flush
    STDERR.flush
    Kernel.exit! 1
  end

  cell = layout.cell(cellName)
  if cell.to_s.empty?
    STDERR.puts "ERROR: couldn't open the cell #{cellName}"
    STDOUT.flush
    STDERR.flush
    Kernel.exit! 1
  end

  puts "cell #{cellName}"
  portLayers.each do |layer_type_it|
    port_layer_info = LayerInfo.from_string(layer_type_it)
    my_layer_index = cell.layout.find_layer(port_layer_info)
    if my_layer_index
       puts "Found #{port_layer_info}"
       my_shapes = cell.shapes(my_layer_index)
       my_shapes.each do |shape_it|
          if shape_it.is_text?
             puts "text: #{shape_it.text_pos} #{layer_type_it} #{shape_it.text_string}"
          elsif shape_it.is_box?
             puts "box: #{shape_it.box_p1} #{shape_it.box_p2} #{layer_type_it}"
          else
             puts "Unrecognized shape #{shape_it.type}"
          end
       end
    end
  end

end

puts "Done."

# reserve status=1 for I/O errors
if errs > 0
  errs = errs + 1
end
# don't roll-over exit-status to/past zero
if errs > 255
  errs = 255
end

# exit doesn't work to set status; exit! requires explicit buffered-IO flush.
STDOUT.flush
STDERR.flush
Kernel.exit! errs
