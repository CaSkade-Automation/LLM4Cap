package prompting;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class PromptGeneration {

public static String generatePrompt(String nLDescription) {
		
		Path promptTemplate = Paths.get("prompt/prompt-template.txt");
		Path outputPrompt = Paths.get("prompt/prompt.txt");
		Map<String, String> placeholders = new HashMap<String, String>();

        placeholders.put("T-Box", "prompt/cask_cropped.ttl");
        placeholders.put("Example Task 1", "prompt/coffeemaking-task.txt");
        placeholders.put("Example Capability A-Box 1", "prompt/coffeemaking.ttl");
        placeholders.put("Example Task 2", "prompt/multiplication-task.txt");
        placeholders.put("Example Capability A-Box 2", "prompt/multiplication.ttl");
        placeholders.put("Example Task 3", "prompt/distillation-task.txt");
        placeholders.put("Example Capability A-Box 3", "prompt/distillation.ttl");
        placeholders.put("Task", nLDescription);
        
        try {
            String prompt = new String(Files.readAllBytes(promptTemplate));
            prompt = replacePlaceholdersWithFileContent(prompt, placeholders);
            Files.write(outputPrompt, prompt.getBytes());
            return prompt; 
        } catch (IOException e) {
            e.printStackTrace();
            return null; 
        }
	}
	
	private static String replacePlaceholdersWithFileContent(String prompt, Map<String, String> placeholders) throws IOException {
        Pattern pattern = Pattern.compile("\\$\\{(.*?)\\}");
        Matcher matcher = pattern.matcher(prompt);

        while (matcher.find()) {
            String placeholder = matcher.group(1);
            if (placeholders.containsKey(placeholder)) {
            	String replacement; 
            	if (Paths.get(placeholders.get(placeholder)).toFile().exists()) {
            		replacement = new String(Files.readAllBytes(Paths.get(placeholders.get(placeholder))));
            	} else {
            		replacement = placeholders.get(placeholder);
            	}
            	prompt = prompt.replace("${" + placeholder + "}", replacement);
            }
        }
        return prompt;
    }
}
