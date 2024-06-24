package prompting;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;

public class PromptGeneration {

	static String generatePrompt(String nLDescription) throws IOException {
		
		String prompt = readResourceFile("prompt-template.txt"); 
		Map<String, String> placeholders = new HashMap<String, String>();

        placeholders.put("${T-Box}", readResourceFile("cask_cropped.ttl"));
        placeholders.put("${Example Task 1}", readResourceFile("coffeemaking-task.txt"));
        placeholders.put("${Example Capability A-Box 1}", readResourceFile("coffeemaking.ttl"));
        placeholders.put("${Example Task 2}", readResourceFile("multiplication-task.txt"));
        placeholders.put("${Example Capability A-Box 2}", readResourceFile("multiplication.ttl"));
        placeholders.put("${Example Task 3}", readResourceFile("distillation-task.txt"));
        placeholders.put("${Example Capability A-Box 3}", readResourceFile("distillation.ttl"));
        placeholders.put("${Task}", nLDescription);

        for (Map.Entry<String, String> entry : placeholders.entrySet()) {
            prompt = prompt.replace(entry.getKey(), entry.getValue());
        }
        
        return prompt; 
	}

	private static String readResourceFile(String fileName) throws IOException {
		try (InputStream input = PromptingHelper.class.getClassLoader().getResourceAsStream("prompt/" + fileName);
			BufferedReader reader = new BufferedReader(new InputStreamReader(input, StandardCharsets.UTF_8))) {
	            return reader.lines().collect(Collectors.joining(System.lineSeparator()));
		}
	}
}
