package rest_api;

import static spark.Spark.*;

import java.util.Arrays;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.gson.Gson;

import clients.LlmModels;
import prompting.Llm4Cap;

public class RestApi {

	final static int port = 9292;
	private final static Logger logger = LoggerFactory.getLogger(RestApi.class);

	public static void main(String[] args) {
		port(port);
		logger.info("Running LLM Capability Generation on port" + port);

		// Setup a simple ping route. Could in the future return some API info
		get("/ping", (request, response) -> {
			response.status(204);
			return "";
		});

		// Setup a route to return all available models
		get("/models", (request, response) -> {
			// Convert enum to string array
			String[] modelNames = Arrays.stream(LlmModels.values())
                    .map(Enum::name)
                    .toArray(String[]::new); 
			
			// Setzen Sie den Content-Type auf Application/JSON
			response.type("application/json");
			
			// Konvertieren Sie das Array in einen JSON String und geben Sie es zurück
			response.status(200);
			return new Gson().toJson(modelNames);
		});

		
		// Setup a post route at base path
		post("/", (request, response) -> {
			
			// Deserialize body into object
			String body = request.body();
            Gson gson = new Gson();
            CapabilityGenerationRequest req = gson.fromJson(body, CapabilityGenerationRequest.class);

			logger.info("Received new task description. Starting capability generation...");
			String result = Llm4Cap.generateCapability(req.capabilityDescription, LlmModels.valueOf(req.model));
			logger.info("Completed capability generation");
			
			// Setzen Sie den Content-Type auf Application/JSON
			response.type("text/turtle");
			
			return result;
		});
	}

}
