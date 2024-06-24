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

	/**
	 * Takes the prompt template and fills it with all the content for T-Box, examples and the actual task description
	 * @param taskDescription The natural language task description used to generate a capability description
	 * @return
	 * @throws IOException thrown in case the prompt-template file cannot be found or opened
	 */
	public static String generatePrompt(String taskDescription) {
		// Open template file
		String prompt = null;
		prompt = readResourceFile("prompt-template.txt");
		
		// Put all placeholders and their contents in a map
		Map<String, String> placeholders = new HashMap<String, String>();
        placeholders.put("${T-Box}", readResourceFile("cask_cropped.ttl"));
        placeholders.put("${Example Task 1}", readResourceFile("coffeemaking-task.txt"));
        placeholders.put("${Example Capability A-Box 1}", readResourceFile("coffeemaking.ttl"));
        placeholders.put("${Example Task 2}", readResourceFile("multiplication-task.txt"));
        placeholders.put("${Example Capability A-Box 2}", readResourceFile("multiplication.ttl"));
        placeholders.put("${Example Task 3}", readResourceFile("distillation-task.txt"));
        placeholders.put("${Example Capability A-Box 3}", readResourceFile("distillation.ttl"));
        placeholders.put("${Task}", taskDescription);

        // Replace each placeholder with its value 
        for (Map.Entry<String, String> entry : placeholders.entrySet()) {
            prompt = prompt.replace(entry.getKey(), entry.getValue());
        }
        
        // Return completed prompt without placeholders
        return prompt; 
	}

	/**
	 * Little utility function to open files and read them as a String
	 * @param fileName
	 * @return
	 * @throws IOException
	 */
	private static String readResourceFile(String fileName) {
		InputStream input = PromptGeneration.class.getClassLoader().getResourceAsStream("prompt/" + fileName);
		BufferedReader reader = new BufferedReader(new InputStreamReader(input, StandardCharsets.UTF_8));
        return reader.lines().collect(Collectors.joining(System.lineSeparator()));
	}
}
