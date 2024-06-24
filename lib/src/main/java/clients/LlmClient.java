package clients;

import java.io.FileInputStream;
import java.io.IOException;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Paths;
import java.util.Properties;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Abstract base class for all LLM clients holding some base functionalities and defining some abstract methods
 */
public abstract class LlmClient {
	final String CONFIG_FILE_NAME = "config.properties";
	protected static final Logger logger = LoggerFactory.getLogger(LlmClient.class);
	protected LlmModels model;
	protected HttpClient client;
	
	public LlmClient(LlmModels model) {
		this.model = model;
		this.client = HttpClient.newBuilder()
				.version(HttpClient.Version.HTTP_2)
				.build();
	}
	
	abstract public String generateCapability(String prompt);
	
	protected String loadApiKey(String keyName) throws Exception {
		String jarPath = Paths.get("").toAbsolutePath().toString();
		String configFilePath = Paths.get(jarPath, CONFIG_FILE_NAME).toString();
		logger.info(configFilePath);

		try (FileInputStream input = new FileInputStream(configFilePath)) {
			Properties prop = new Properties();
			prop.load(input);

			String apiKey;
			apiKey = prop.getProperty(keyName);
			if (apiKey == null || apiKey.trim().isEmpty()) {
				logger.error("API key not found in config.properties");
				throw new Exception("API key with name " + keyName + "not found in config.properties. Make sure to provide the key to use the corresponding LLM");
			}
			return apiKey;

		} catch (IOException e) {
			throw new Exception("Unable to find config.properties. Make sure to have a config.properties file next to your JAR");
		}
	}
	
	String executeRequest(HttpRequest request) {
    	try {
            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
            logger.info("Status Code: " + response.statusCode());
            return response.body();
        } catch (Exception e) {
            e.printStackTrace();
        }
		return "";
	}

}
