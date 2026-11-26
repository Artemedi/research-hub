using System;
using System.IO;
using System.Linq;
using System.Reflection.Metadata;
using System.Reflection.Metadata.Ecma335;
using System.Reflection.PortableExecutable;
using System.Text.Json;

using var file = File.OpenRead(args[0]);
using var pe = new PEReader(file);
var metadata = pe.GetMetadataReader();

string Token(EntityHandle handle) => $"0x{MetadataTokens.GetToken(handle):x8}";

int Offset(TableIndex table, int row) =>
    pe.PEHeaders.MetadataStartOffset + metadata.GetTableMetadataOffset(table)
    + (row - 1) * metadata.GetTableRowSize(table);

var module = metadata.GetModuleDefinition();
var assembly = metadata.GetAssemblyDefinition();
Console.WriteLine(JsonSerializer.Serialize(new
{
    module = new {
        name = metadata.GetString(module.Name),
        mvid = metadata.GetGuid(module.Mvid),
        token = Token(MetadataTokens.EntityHandle(TableIndex.Module, 1)),
        row_offset = Offset(TableIndex.Module, 1)
    },
    assembly = new {
        name = metadata.GetString(assembly.Name),
        version = assembly.Version.ToString(),
        token = Token(MetadataTokens.EntityHandle(TableIndex.Assembly, 1)),
        row_offset = Offset(TableIndex.Assembly, 1)
    },
    references = metadata.AssemblyReferences.Select(handle =>
    {
        var reference = metadata.GetAssemblyReference(handle);
        return new {
            name = metadata.GetString(reference.Name),
            version = reference.Version.ToString(),
            token = Token(handle),
            row_offset = Offset(TableIndex.AssemblyRef, MetadataTokens.GetRowNumber(handle))
        };
    }),
    row_counts = new {
        TypeDef = metadata.GetTableRowCount(TableIndex.TypeDef),
        MethodDef = metadata.GetTableRowCount(TableIndex.MethodDef)
    }
}));
