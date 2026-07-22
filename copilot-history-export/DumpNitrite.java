import org.dizitart.no2.Nitrite;
import org.dizitart.no2.collection.Document;
import org.dizitart.no2.collection.NitriteCollection;
import org.dizitart.no2.collection.NitriteId;
import org.dizitart.no2.mvstore.MVStoreModule;
import org.dizitart.no2.store.NitriteMap;
import org.dizitart.no2.store.NitriteStore;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.nio.file.*;
import java.util.*;

/**
 * Read a Copilot nitrite session DB and dump every collection to JSON.
 * Usage: java DumpNitrite <input.db> <output-dir>
 */
public class DumpNitrite {
    public static void main(String[] args) throws Exception {
        if (args.length != 2) {
            System.err.println("usage: DumpNitrite <input.db> <output-dir>");
            System.exit(2);
        }
        Path input = Paths.get(args[0]).toAbsolutePath();
        Path outDir = Paths.get(args[1]).toAbsolutePath();
        Files.createDirectories(outDir);

        // Work on a COPY (read-only would still risk journal writes on some MVStore versions).
        Path tmp = Files.createTempFile("copilot-nitrite-", ".db");
        Files.copy(input, tmp, StandardCopyOption.REPLACE_EXISTING);

        MVStoreModule mv = MVStoreModule.withConfig()
                .filePath(tmp.toFile())
                .readOnly(true)
                .build();

        Nitrite db = Nitrite.builder()
                .loadModule(mv)
                .fieldSeparator(".")
                .openOrCreate();

        ObjectMapper om = new ObjectMapper();
        om.enable(SerializationFeature.INDENT_OUTPUT);

        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("source", input.toString());

        // Standalone collections
        List<Map<String, Object>> collInfo = new ArrayList<>();
        for (String name : db.listCollectionNames()) {
            NitriteCollection c = db.getCollection(name);
            List<Object> docs = new ArrayList<>();
            for (Document d : c.find()) {
                docs.add(toPlain(d));
            }
            Path out = outDir.resolve("collection__" + safeName(name) + ".json");
            om.writeValue(out.toFile(), docs);
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("name", name);
            row.put("count", docs.size());
            row.put("file", out.getFileName().toString());
            collInfo.add(row);
        }
        summary.put("collections", collInfo);

        // Object repositories (agent sessions live here). Bypass the ObjectRepository API
        // (which needs the entity class + Jackson mapping) and read the raw NitriteMap.
        NitriteStore<?> store = db.getStore();
        List<Map<String, Object>> repoInfo = new ArrayList<>();
        for (String repoName : db.listRepositories()) {
            List<Object> docs = new ArrayList<>();
            String err = null;
            try {
                NitriteMap<NitriteId, Document> map = store.openMap(repoName, NitriteId.class, Document.class);
                for (Document d : map.values()) {
                    docs.add(toPlain(d));
                }
            } catch (Throwable t) {
                err = t.getClass().getName() + ": " + t.getMessage();
            }
            Path out = outDir.resolve("repo__" + safeName(repoName) + ".json");
            om.writeValue(out.toFile(), docs);
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("name", repoName);
            row.put("count", docs.size());
            row.put("file", out.getFileName().toString());
            if (err != null) row.put("error", err);
            repoInfo.add(row);
        }
        summary.put("repositories", repoInfo);

        try (PrintWriter pw = new PrintWriter(new FileWriter(outDir.resolve("_summary.json").toFile()))) {
            pw.println(om.writeValueAsString(summary));
        }

        db.close();
        Files.deleteIfExists(tmp);
    }

    private static String safeName(String n) {
        return n.replaceAll("[^A-Za-z0-9._+-]", "_");
    }

    /** Recursively convert Nitrite Document (a Map) into plain Java types Jackson can handle. */
    private static Object toPlain(Object o) {
        if (o == null) return null;
        if (o instanceof Document d) {
            LinkedHashMap<String, Object> m = new LinkedHashMap<>();
            for (String k : d.getFields()) m.put(k, toPlain(d.get(k)));
            return m;
        }
        if (o instanceof Map<?, ?> mm) {
            LinkedHashMap<String, Object> m = new LinkedHashMap<>();
            for (var e : mm.entrySet()) m.put(String.valueOf(e.getKey()), toPlain(e.getValue()));
            return m;
        }
        if (o instanceof Collection<?> c) {
            List<Object> out = new ArrayList<>(c.size());
            for (var x : c) out.add(toPlain(x));
            return out;
        }
        if (o.getClass().isArray()) {
            int n = java.lang.reflect.Array.getLength(o);
            List<Object> out = new ArrayList<>(n);
            for (int i = 0; i < n; i++) out.add(toPlain(java.lang.reflect.Array.get(o, i)));
            return out;
        }
        if (o instanceof CharSequence || o instanceof Number || o instanceof Boolean) return o;
        if (o instanceof java.util.Date || o instanceof java.time.temporal.TemporalAccessor) return o.toString();
        // Fallback: coerce to string so Jackson never chokes on plugin-internal types.
        return o.toString();
    }
}


